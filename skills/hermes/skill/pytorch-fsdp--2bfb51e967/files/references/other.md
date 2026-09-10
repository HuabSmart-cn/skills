# Pytorch-Fsdp - Other

**Pages:** 15

---

## Distributed Data Parallel#

**URL:** https://pytorch.org/docs/stable/notes/ddp.html

**Contents:**
- Distributed Data Parallel#
- Example#
- Internal Design#
- Implementation#
  - ProcessGroup#
  - DistributedDataParallel#
  - TorchDynamo DDPOptimizer#

Created On: Jan 15, 2020 | Last Updated On: Jan 25, 2024

The implementation of torch.nn.parallel.DistributedDataParallel evolves over time. This design note is written based on the state as of v1.4.

torch.nn.parallel.DistributedDataParallel (DDP) transparently performs distributed data parallel training. This page describes how it works and reveals implementation details.

Let us start with a simple torch.nn.parallel.DistributedDataParallel example. This example uses a torch.nn.Linear as the local model, wraps it with DDP, and then runs one forward pass, one backward pass, and an optimizer step on the DDP model. After that, parameters on the local model will be updated, and all models on different processes should be exactly the same.

DDP works with TorchDynamo. When used with TorchDynamo, apply the DDP model wrapper before compiling the model, such that torchdynamo can apply DDPOptimizer (graph-break optimizations) based on DDP bucket sizes. (See TorchDynamo DDPOptimizer for more information.)

This section reveals how it works under the hood of torch.nn.parallel.DistributedDataParallel by diving into details of every step in one iteration.

Prerequisite: DDP relies on c10d ProcessGroup for communications. Hence, applications must create ProcessGroup instances before constructing DDP.

Construction: The DDP constructor takes a reference to the local module, and broadcasts state_dict() from the process with rank 0 to all other processes in the group to make sure that all model replicas start from the exact same state. Then, each DDP process creates a local Reducer, which later will take care of the gradients synchronization during the backward pass. To improve communication efficiency, the Reducer organizes parameter gradients into buckets, and reduces one bucket at a time. Bucket size can be configured by setting the bucket_cap_mb argument in DDP constructor. The mapping from parameter gradients to buckets is determined at the construction time, based on the bucket size limit and parameter sizes. Model parameters are allocated into buckets in (roughly) the reverse order of Model.parameters() from the given model. The reason for using the reverse order is because DDP expects gradients to become ready during the backward pass in approximately that order. The figure below shows an example. Note that, the grad0 and grad1 are in bucket1, and the other two gradients are in bucket0. Of course, this assumption might not always be true, and when that happens it could hurt DDP backward speed as the Reducer cannot kick off the communication at the earliest possible time. Besides bucketing, the Reducer also registers autograd hooks during construction, one hook per parameter. These hooks will be triggered during the backward pass when the gradient becomes ready.

Forward Pass: The DDP takes the input and passes it to the local model, and then analyzes the output from the local model if find_unused_parameters is set to True. This mode allows running backward on a subgraph of the model, and DDP finds out which parameters are involved in the backward pass by traversing the autograd graph from the model output and marking all unused parameters as ready for reduction. During the backward pass, the Reducer would only wait for unready parameters, but it would still reduce all buckets. Marking a parameter gradient as ready does not help DDP skip buckets as for now, but it will prevent DDP from waiting for absent gradients forever during the backward pass. Note that traversing the autograd graph introduces extra overheads, so applications should only set find_unused_parameters to True when necessary.

Backward Pass: The backward() function is directly invoked on the loss Tensor, which is out of DDP’s control, and DDP uses autograd hooks registered at construction time to trigger gradients synchronizations. When one gradient becomes ready, its corresponding DDP hook on that grad accumulator will fire, and DDP will then mark that parameter gradient as ready for reduction. When gradients in one bucket are all ready, the Reducer kicks off an asynchronous allreduce on that bucket to calculate mean of gradients across all processes. When all buckets are ready, the Reducer will block waiting for all allreduce operations to finish. When this is done, averaged gradients are written to the param.grad field of all parameters. So after the backward pass, the grad field on the same corresponding parameter across different DDP processes should be the same.

Optimizer Step: From the optimizer’s perspective, it is optimizing a local model. Model replicas on all DDP processes can keep in sync because they all start from the same state and they have the same averaged gradients in every iteration.

DDP requires Reducer instances on all processes to invoke allreduce in exactly the same order, which is done by always running allreduce in the bucket index order instead of actual bucket ready order. Mismatched allreduce order across processes can lead to wrong results or DDP backward hang.

Below are pointers to the DDP implementation components. The stacked graph shows the structure of the code.

ProcessGroup.hpp: contains the abstract API of all process group implementations. The c10d library provides 3 implementations out of the box, namely, ProcessGroupGloo, ProcessGroupNCCL, and ProcessGroupMPI. DistributedDataParallel uses ProcessGroup::broadcast() to send model states from the process with rank 0 to others during initialization and ProcessGroup::allreduce() to sum gradients.

Store.hpp: assists the rendezvous service for process group instances to find each other.

distributed.py: is the Python entry point for DDP. It implements the initialization steps and the forward function for the nn.parallel.DistributedDataParallel module which call into C++ libraries. Its _sync_param function performs intra-process parameter synchronization when one DDP process works on multiple devices, and it also broadcasts model buffers from the process with rank 0 to all other processes. The inter-process parameter synchronization happens in Reducer.cpp.

comm.h: implements the coalesced broadcast helper function which is invoked to broadcast model states during initialization and synchronize model buffers before the forward pass.

reducer.h: provides the core implementation for gradient synchronization in the backward pass. It has three entry point functions:

Reducer: The constructor is called in distributed.py which registers Reducer::autograd_hook() to gradient accumulators.

autograd_hook() function will be invoked by the autograd engine when a gradient becomes ready.

prepare_for_backward() is called at the end of DDP forward pass in distributed.py. It traverses the autograd graph to find unused parameters when find_unused_parameters is set to True in DDP constructor.

DDP’s performance advantage comes from overlapping allreduce collectives with computations during backwards. AotAutograd prevents this overlap when used with TorchDynamo for compiling a whole forward and whole backward graph, because allreduce ops are launched by autograd hooks _after_ the whole optimized backwards computation finishes.

TorchDynamo’s DDPOptimizer helps by breaking the forward graph at the logical boundaries of DDP’s allreduce buckets during backwards. Note: the goal is to break the graph during backwards, and the simplest implementation is to break the forward graphs and then call AotAutograd and compilation on each section. This allows DDP’s allreduce hooks to fire in-between sections of backwards, and schedule communications to overlap with compute.

See this blog post for a more in-depth explanation and experimental results, or read the docs and code at torch/_dynamo/optimizations/distributed.py

To Debug DDPOptimizer, set TORCH_LOGS=’ddp_graphs’ for full graph dumps. For logs without graphs, add any of ‘dynamo’, ‘distributed’, or ‘dist_ddp’ to TORCH_LOGS (for basic info about bucket boundaries). To disable DDPOptimizer, set torch._dynamo.config.optimize_ddp=False. DDP and TorchDynamo should still work correctly without DDPOptimizer, but with performance degradation.

---

## PyTorch documentation#

**URL:** https://pytorch.org/docs/stable/

**Contents:**
- PyTorch documentation#
- Indices and tables#

PyTorch is an optimized tensor library for deep learning using GPUs and CPUs.

Features described in this documentation are classified by release status:

Stable (API-Stable): These features will be maintained long-term and there should generally be no major performance limitations or gaps in documentation. We also expect to maintain backwards compatibility (although breaking changes can happen and notice will be given one release ahead of time).

Unstable (API-Unstable): Encompasses all features that are under active development where APIs may change based on user feedback, requisite performance improvements or because coverage across operators is not yet complete. The APIs and performance characteristics of these features may change.

---

## Generic Join Context Manager#

**URL:** https://pytorch.org/docs/stable/distributed.algorithms.join.html

**Contents:**
- Generic Join Context Manager#

Created On: Jun 06, 2025 | Last Updated On: Jun 06, 2025

The generic join context manager facilitates distributed training on uneven inputs. This page outlines the API of the relevant classes: Join, Joinable, and JoinHook. For a tutorial, see Distributed Training with Uneven Inputs Using the Join Context Manager.

This class defines the generic join context manager, which allows custom hooks to be called after a process joins.

These hooks should shadow the collective communications of non-joined processes to prevent hanging and erroring and to ensure algorithmic correctness. Refer to JoinHook for details about the hook definition.

The context manager requires each participating Joinable to call the method notify_join_context() before its own per- iteration collective communications to ensure correctness.

The context manager requires that all process_group attributes in the JoinHook objects are the same. If there are multiple JoinHook objects, then the device of the first is used. The process group and device information is used for checking for non- joined processes and for notifying processes to throw an exception if throw_on_early_termination is enabled, both of which using an all- reduce.

joinables (List[Joinable]) – a list of the participating Joinable s; their hooks are iterated over in the given order.

enable (bool) – a flag enabling uneven input detection; setting to False disables the context manager’s functionality and should only be set when the user knows the inputs will not be uneven (default: True).

throw_on_early_termination (bool) – a flag controlling whether to throw an exception upon detecting uneven inputs (default: False).

Notifies the join context manager that the calling process has not yet joined.

Then, if throw_on_early_termination=True, checks if uneven inputs have been detected (i.e. if one process has already joined) and throws an exception if so.

This method should be called from a Joinable object before its per-iteration collective communications. For example, this should be called at the beginning of the forward pass in DistributedDataParallel.

Only the first Joinable object passed into the context manager performs the collective communications in this method, and for the others, this method is vacuous.

joinable (Joinable) – the Joinable object calling this method.

An async work handle for the all-reduce meant to notify the context manager that the process has not yet joined if joinable is the first one passed into the context manager; None otherwise.

This defines an abstract base class for joinable classes.

A joinable class (inheriting from Joinable) should implement join_hook(), which returns a JoinHook instance, in addition to join_device() and join_process_group() that return device and process group information, respectively.

Return the device from which to perform collective communications needed by the join context manager.

Return a JoinHook instance for the given Joinable.

kwargs (dict) – a dict containing any keyword arguments to modify the behavior of the join hook at run time; all Joinable instances sharing the same join context manager are forwarded the same value for kwargs.

Returns the process group for the collective communications needed by the join context manager itself.

This defines a join hook, which provides two entry points in the join context manager.

Entry points : a main hook, which is called repeatedly while there exists a non-joined process, and a post-hook, which is called once all processes have joined.

To implement a join hook for the generic join context manager, define a class that inherits from JoinHook and override main_hook() and post_hook() as appropriate.

Call this hook while there exists a non-joined process to shadow collective communications in a training iteration.

Training iteration i.e., in one forward pass, backward pass, and optimizer step.

Call hook after all processes have joined.

It is passed an additional bool argument is_last_joiner, which indicates if the rank is one of the last to join.

is_last_joiner (bool) – True if the rank is one of the last to join; False otherwise.

---

## Experimental Object Oriented Distributed API#

**URL:** https://pytorch.org/docs/stable/distributed._dist2.html

**Contents:**
- Experimental Object Oriented Distributed API#

Created On: Jul 09, 2025 | Last Updated On: Jul 30, 2025

This is an experimental new API for PyTorch Distributed. This is actively in development and subject to change or deletion entirely.

This is intended as a proving ground for more flexible and object oriented distributed APIs.

Bases: pybind11_object

A ProcessGroup is a communication primitive that allows for collective operations across a group of processes.

This is a base class that provides the interface for all ProcessGroups. It is not meant to be used directly, but rather extended by subclasses.

Bases: pybind11_object

The type of the backend used for the process group.

abort all operations and connections if supported by the backend

allgather(self: torch._C._distributed_c10d.ProcessGroup, output_tensors: collections.abc.Sequence[collections.abc.Sequence[torch.Tensor]], input_tensors: collections.abc.Sequence[torch.Tensor], opts: torch._C._distributed_c10d.AllgatherOptions = <torch._C._distributed_c10d.AllgatherOptions object at 0x7f0162b6b9b0>) -> c10d::Work

Allgathers the input tensors from all processes across the process group.

See torch.distributed.all_gather() for more details.

allgather(self: torch._C._distributed_c10d.ProcessGroup, output_tensors: collections.abc.Sequence[torch.Tensor], input_tensor: torch.Tensor, timeout: datetime.timedelta | None = None) -> c10d::Work

Allgathers the input tensors from all processes across the process group.

See torch.distributed.all_gather() for more details.

Allgathers the input tensors from all processes across the process group.

See torch.distributed.all_gather() for more details.

Allgathers the input tensors from all processes across the process group.

See torch.distributed.all_gather() for more details.

allreduce(self: torch._C._distributed_c10d.ProcessGroup, tensors: collections.abc.Sequence[torch.Tensor], opts: torch._C._distributed_c10d.AllreduceOptions = <torch._C._distributed_c10d.AllreduceOptions object at 0x7f0162745db0>) -> c10d::Work

Allreduces the provided tensors across all processes in the process group.

See torch.distributed.all_reduce() for more details.

allreduce(self: torch._C._distributed_c10d.ProcessGroup, tensors: collections.abc.Sequence[torch.Tensor], op: torch._C._distributed_c10d.ReduceOp = <RedOpType.SUM: 0>, timeout: datetime.timedelta | None = None) -> c10d::Work

Allreduces the provided tensors across all processes in the process group.

See torch.distributed.all_reduce() for more details.

allreduce(self: torch._C._distributed_c10d.ProcessGroup, tensor: torch.Tensor, op: torch._C._distributed_c10d.ReduceOp = <RedOpType.SUM: 0>, timeout: datetime.timedelta | None = None) -> c10d::Work

Allreduces the provided tensors across all processes in the process group.

See torch.distributed.all_reduce() for more details.

Allreduces the provided tensors across all processes in the process group.

See torch.distributed.all_reduce() for more details.

Alltoalls the input tensors from all processes across the process group.

See torch.distributed.all_to_all() for more details.

alltoall_base(self: torch._C._distributed_c10d.ProcessGroup, output: torch.Tensor, input: torch.Tensor, output_split_sizes: collections.abc.Sequence[typing.SupportsInt], input_split_sizes: collections.abc.Sequence[typing.SupportsInt], opts: torch._C._distributed_c10d.AllToAllOptions = <torch._C._distributed_c10d.AllToAllOptions object at 0x7f0162b79d30>) -> c10d::Work

Alltoalls the input tensors from all processes across the process group.

See torch.distributed.all_to_all() for more details.

alltoall_base(self: torch._C._distributed_c10d.ProcessGroup, output: torch.Tensor, input: torch.Tensor, output_split_sizes: collections.abc.Sequence[typing.SupportsInt], input_split_sizes: collections.abc.Sequence[typing.SupportsInt], timeout: datetime.timedelta | None = None) -> c10d::Work

Alltoalls the input tensors from all processes across the process group.

See torch.distributed.all_to_all() for more details.

barrier(self: torch._C._distributed_c10d.ProcessGroup, opts: torch._C._distributed_c10d.BarrierOptions = <torch._C._distributed_c10d.BarrierOptions object at 0x7f0162745ab0>) -> c10d::Work

then all leave the call together.

See torch.distributed.barrier() for more details.

barrier(self: torch._C._distributed_c10d.ProcessGroup, timeout: datetime.timedelta | None = None) -> c10d::Work

then all leave the call together.

See torch.distributed.barrier() for more details.

broadcast(self: torch._C._distributed_c10d.ProcessGroup, tensors: collections.abc.Sequence[torch.Tensor], opts: torch._C._distributed_c10d.BroadcastOptions = <torch._C._distributed_c10d.BroadcastOptions object at 0x7f0162b7afb0>) -> c10d::Work

Broadcasts the tensor to all processes in the process group.

See torch.distributed.broadcast() for more details.

broadcast(self: torch._C._distributed_c10d.ProcessGroup, tensor: torch.Tensor, root: typing.SupportsInt, timeout: datetime.timedelta | None = None) -> c10d::Work

Broadcasts the tensor to all processes in the process group.

See torch.distributed.broadcast() for more details.

gather(self: torch._C._distributed_c10d.ProcessGroup, output_tensors: collections.abc.Sequence[collections.abc.Sequence[torch.Tensor]], input_tensors: collections.abc.Sequence[torch.Tensor], opts: torch._C._distributed_c10d.GatherOptions = <torch._C._distributed_c10d.GatherOptions object at 0x7f0162c301f0>) -> c10d::Work

Gathers the input tensors from all processes across the process group.

See torch.distributed.gather() for more details.

gather(self: torch._C._distributed_c10d.ProcessGroup, output_tensors: collections.abc.Sequence[torch.Tensor], input_tensor: torch.Tensor, root: typing.SupportsInt, timeout: datetime.timedelta | None = None) -> c10d::Work

Gathers the input tensors from all processes across the process group.

See torch.distributed.gather() for more details.

Get the store of this process group.

Gets this process group description

(Gets this process group name. It’s cluster unique)

then all leave the call together.

See torch.distributed.monitored_barrier() for more details.

Get the name of this process group.

Get the rank of this process group.

Receives the tensor from the specified rank.

See torch.distributed.recv() for more details.

Receives the tensor from any source.

See torch.distributed.recv() for more details.

reduce(self: torch._C._distributed_c10d.ProcessGroup, tensors: collections.abc.Sequence[torch.Tensor], opts: torch._C._distributed_c10d.ReduceOptions = <torch._C._distributed_c10d.ReduceOptions object at 0x7f0162bce3f0>) -> c10d::Work

Reduces the provided tensors across all processes in the process group.

See torch.distributed.reduce() for more details.

reduce(self: torch._C._distributed_c10d.ProcessGroup, tensor: torch.Tensor, root: typing.SupportsInt, op: torch._C._distributed_c10d.ReduceOp = <RedOpType.SUM: 0>, timeout: datetime.timedelta | None = None) -> c10d::Work

Reduces the provided tensors across all processes in the process group.

See torch.distributed.reduce() for more details.

reduce_scatter(self: torch._C._distributed_c10d.ProcessGroup, output_tensors: collections.abc.Sequence[torch.Tensor], input_tensors: collections.abc.Sequence[collections.abc.Sequence[torch.Tensor]], opts: torch._C._distributed_c10d.ReduceScatterOptions = <torch._C._distributed_c10d.ReduceScatterOptions object at 0x7f0162ee5cf0>) -> c10d::Work

Reduces and scatters the input tensors from all processes across the process group.

See torch.distributed.reduce_scatter() for more details.

reduce_scatter(self: torch._C._distributed_c10d.ProcessGroup, output: torch.Tensor, input: collections.abc.Sequence[torch.Tensor], op: torch._C._distributed_c10d.ReduceOp = <RedOpType.SUM: 0>, timeout: datetime.timedelta | None = None) -> c10d::Work

Reduces and scatters the input tensors from all processes across the process group.

See torch.distributed.reduce_scatter() for more details.

Reduces and scatters the input tensors from all processes across the process group.

See torch.distributed.reduce_scatter() for more details.

scatter(self: torch._C._distributed_c10d.ProcessGroup, output_tensors: collections.abc.Sequence[torch.Tensor], input_tensors: collections.abc.Sequence[collections.abc.Sequence[torch.Tensor]], opts: torch._C._distributed_c10d.ScatterOptions = <torch._C._distributed_c10d.ScatterOptions object at 0x7f0162b879f0>) -> c10d::Work

Scatters the input tensors from all processes across the process group.

See torch.distributed.scatter() for more details.

scatter(self: torch._C._distributed_c10d.ProcessGroup, output_tensor: torch.Tensor, input_tensors: collections.abc.Sequence[torch.Tensor], root: typing.SupportsInt, timeout: datetime.timedelta | None = None) -> c10d::Work

Scatters the input tensors from all processes across the process group.

See torch.distributed.scatter() for more details.

Sends the tensor to the specified rank.

See torch.distributed.send() for more details.

Sets the default timeout for all future operations.

shutdown the process group

Get the size of this process group.

Protocol for process group factories.

Get the current process group. Thread local method.

The current process group.

Create a new process group with the given backend and options. This group is independent and will not be globally registered and thus not usable via the standard torch.distributed.* APIs.

backend (str) – The backend to use for the process group.

timeout (timedelta) – The timeout for collective operations.

device (Union[str, device]) – The device to use for the process group.

**kwargs (object) – All remaining arguments are passed to the backend constructor. See the backend specific documentation for details.

Context manager for process groups. Thread local method.

pg (ProcessGroup) – The process group to use.

Generator[None, None, None]

Register a new process group backend.

name (str) – The name of the backend.

func (ProcessGroupFactory) – The function to create the process group.

---

## torch.distributed.fsdp.fully_shard#

**URL:** https://pytorch.org/docs/stable/distributed.fsdp.fully_shard.html

**Contents:**
- torch.distributed.fsdp.fully_shard#
- PyTorch FSDP2 (fully_shard)#

Created On: Dec 04, 2024 | Last Updated On: Jun 16, 2025

PyTorch FSDP2 (RFC) provides a fully sharded data parallelism (FSDP) implementation targeting performant eager-mode while using per-parameter sharding for improved usability

See the Getting Started with FSDP2 tutorial for more information.

If you are currently using FSDP1, consider migrating to FSDP2 using our migration guide.

The user contract for fully_shard(model) is as follows

For model initialization, fully_shard converts model.parameters() from plain torch.Tensor to DTensor in-place. The parameters are moved to the appropriate device according to the device mesh.

Before forward and backward passes, pre-forward/backward hooks are responsible for all-gathering the parameters and converting model.parameters() from DTensor to plain torch.Tensor.

After forward and backward passes, post-forward/backward hooks free the unsharded parameters

... [Content truncated, total 335,712 chars] ...