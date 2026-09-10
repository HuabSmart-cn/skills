# UI Integration Guide for Zoom Video SDK Windows

This guide covers three different UI approaches for integrating the Zoom Video SDK:

1. **Win32 (Native C++)** - Direct SDK usage, no wrapper
2. **WinForms (C# .NET)** - Requires C++/CLI wrapper
3. **WPF (C# .NET)** - Requires C++/CLI wrapper + BitmapSource conversion

## Quick Comparison

| Aspect | Win32 | WinForms | WPF |
|--------|-------|----------|-----|
| **Language** | C++ | C# | C# |
| **Wrapper Required** | No | Yes (C++/CLI) | Yes (C++/CLI) |
| **Video Rendering** | Canvas API (SDK renders) | Raw Data Pipe (you render) | Raw Data Pipe + BitmapSource |
| **Performance** | Best | Good | Good (extra conversion) |
| **Complexity** | Medium | Medium | Higher |
| **UI Threading** | Win32 message loop | `InvokeRequired` | `Dispatcher` |

---

## Option 1: Win32 (Native C++) - Direct SDK

**No wrapper needed.** The SDK is native C++, so Win32 apps use it directly.

### Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Win32 Dialog  │────►│  Native C++ SDK │
│   (main.cpp)    │◄────│  (videosdk.dll) │
└─────────────────┘     └─────────────────┘
       HWND              Canvas API
```

### Key Patterns

#### 1. SDK Manager Class (Native C++)

```cpp
// ZoomSDKManager.h
class ZoomSDKManager {
private:
    IZoomVideoSDK* m_pZoomSDK;
    IZoomVideoSDKSession* m_pSession;
    CustomZoomDelegate* m_pDelegate;

public:
    bool Initialize();
    bool JoinSession(const std::string& name, const std::string& token, ...);
    bool StartVideo();
    bool StartVideoPreview(HWND hwnd);  // Canvas API!
    bool SubscribeRemoteVideo(HWND hwnd, const std::string& userId);
};
```

#### 2. Delegate Implementation (All 80+ Callbacks)

```cpp
class CustomZoomDelegate : public IZoomVideoSDKDelegate {
private:
    ZoomSDKManager* m_pManager;

public:
    void onSessionJoin() override {
        m_pManager->OnSessionStatusChanged(SessionStatus::InSession, "Joined");
    }

    void onUserVideoStatusChanged(IZoomVideoSDKVideoHelper* helper,
                                  IVideoSDKVector<IZoomVideoSDKUser*>* userList) override {
        // Handle video status changes
    }

    // ... implement all 80+ callbacks
};
```

#### 3. Video Rendering with Canvas API (SDK-Rendered)

```cpp
// Start video preview - SDK renders directly to HWND
bool ZoomSDKManager::StartVideoPreview(HWND hwnd) {
    IZoomVideoSDKVideoHelper* videoHelper = m_pZoomSDK->getVideoHelper();

    // SDK renders directly to the window handle
    ZoomVideoSDKErrors ret = videoHelper->startVideoCanvasPreview(hwnd);
    return ret == ZoomVideoSDKErrors_Success;
}

// Subscribe to remote user's video
bool ZoomSDKManager::SubscribeRemoteVideo(HWND hwnd, const std::string& userId) {
    IZoomVideoSDKSession* session = m_pZoomSDK->getSessionInfo();
    IVideoSDKVector<IZoomVideoSDKUser*>* userList = session->getRemoteUsers();

    for (int i = 0; i < userList->GetCount(); i++) {
        IZoomVideoSDKUser* user = userList->GetItem(i);
        IZoomVideoSDKCanvas* canvas = user->GetVideoCanvas();

        // SDK renders remote video directly to HWND
        canvas->subscribeWithView(hwnd, ZoomVideoSDKVideoAspect_Original, ZoomVideoSDKResolution_Auto);
    }
    return true;
}
```

#### 4. Win32 Dialog with Video Panels

```cpp
// main.cpp - Dialog procedure
INT_PTR CALLBACK MainDialogProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_INITDIALOG:
        InitializeZoomSDK();
        PopulateDeviceLists(hDlg);
        return TRUE;

    case WM_COMMAND:
        switch (LOWORD(wParam)) {
        case IDC_START_VIDEO:
            g_pSDKManager->StartVideo();

            // Get HWND of video panel control
            HWND selfVideoHwnd = GetDlgItem(hDlg, IDC_SELF_VIDEO);
            g_pSDKManager->StartVideoPreview(selfVideoHwnd);

            HWND remoteVideoHwnd = GetDlgItem(hDlg, IDC_REMOTE_VIDEO);
            g_pSDKManager->SubscribeRemoteVideo(remoteVideoHwnd, "");
            break;
        }
    }
    return FALSE;
}
```

### Win32 Flow Summary

```
1. CreateZoomVideoSDKObj()
2. Initialize SDK with params
3. Create & register CustomZoomDelegate
4. Join session
5. On IDC_START_VIDEO click:
   - startVideo() → transmit your camera
   - startVideoCanvasPreview(selfHwnd) → see yourself
   - subscribeWithView(remoteHwnd) → see others
6. SDK renders directly to HWNDs
```

### Sample Location
```
C:\tempsdk\videosdk-windows-dotnet-desktop-framework-quickstart\
  └── ZoomVideoSDK.Win32\
      ├── main.cpp              # Win32 dialog + event handlers
      ├── ZoomSDKManager.cpp    # SDK wrapper class
      ├── ZoomSDKManager.h      # Header with delegate
      └── main.rc               # Dialog resources
```

---

## Option 2: WinForms (C# + C++/CLI Wrapper)

**Requires C++/CLI bridge** because Zoom SDK is native C++.

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   C# WinForms   │────►│  C++/CLI Wrapper│────►│  Native C++ SDK │
│   (MainForm.cs) │◄────│  (ZoomSDKManager)│◄────│  (videosdk.dll) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     Events              gcroot<T^>               Callbacks
     Bitmap^             YUV→RGB                  YUVRawDataI420
```

### Key Patterns

#### 1. C++/CLI Wrapper Class

```cpp
// ZoomSDKManager.h (C++/CLI)
public ref class ZoomSDKManager {
private:
    void* m_pVideoSDK;              // Hide native types
    void* m_pSessionHandler;        // Native callback handler

public:
    // Managed events for C# consumption
    event EventHandler<SessionStatusEventArgs^>^ SessionStatusChanged;
    event EventHandler<VideoFrameEventArgs^>^ PreviewVideoReceived;
    event EventHandler<VideoFrameEventArgs^>^ RemoteVideoReceived;

    bool Initialize();
    bool JoinSession(String^ name, String^ token, String^ user, String^ pw);
    bool StartVideo();
};
```

#### 2. Native Callback → Managed Event (gcroot pattern)

```cpp
// Native handler stores managed reference via gcroot
class VideoPreviewHandler : public IZoomVideoSDKRawDataPipeDelegate {
private:
    gcroot<ZoomSDKManager^> m_managedHandler;  // Prevents GC

public:
    VideoPreviewHandler(ZoomSDKManager^ handler) : m_managedHandler(handler) {}

    void onRawDataFrameReceived(YUVRawDataI420* data) override {
        ZoomSDKManager^ handler = static_cast<ZoomSDKManager^>(m_managedHandler);
        if (handler && data) {
            // Convert YUV to Bitmap
            Bitmap^ bitmap = handler->ConvertYUVToBitmap(
                data->GetYBuffer(), data->GetUBuffer(), data->GetVBuffer(),
                data->GetStreamWidth(), data->GetStreamHeight(), ...);

            // Fire managed event
            handler->OnPreviewVideoReceived(bitmap);
        }
    }
};
```

#### 3. YUV→RGB Conversion (LockBits for Performance)

```cpp
Bitmap^ ZoomSDKManager::ConvertYUVToBitmap(char* yBuffer, char* uBuffer, char* vBuffer,
                                           int width, int height, ...) {
    Bitmap^ bitmap = gcnew Bitmap(width, height, PixelFormat::Format24bppRgb);

    // Lock for direct memory access (100x faster than SetPixel)
    BitmapData^ data = bitmap->LockBits(rect, ImageLockMode::WriteOnly, ...);
    unsigned char* rgbPtr = (unsigned char*)data->Scan0.ToPointer();

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            // YUV420 → RGB (ITU-R BT.601)
            int Y = yBuffer[y * yStride + x];
            int U = uBuffer[(y/2) * uStride + (x/2)];
            int V = vBuffer[(y/2) * vStride + (x/2)];

            int R = (298 * (Y-16) + 409 * (V-128) + 128) >> 8;
            int G = (298 * (Y-16) - 100 * (U-128) - 208 * (V-128) + 128) >> 8;
            int B = (298 * (Y-16) + 516 * (U-128) + 128) >> 8;

            // Write BGR (bitmap format)
            rgbPtr[y * stride + x * 3 + 0] = (byte)B;
            rgbPtr[y * stride + x * 3 + 1] = (byte)G;
            rgbPtr[y * stride + x * 3 + 2] = (byte)R;
        }
    }

    bitmap->UnlockBits(data);
    return bitmap;
}
```

#### 4. C# Consumer (WinForms)

```csharp
// MainForm.cs
public partial class MainForm : Form {
    private ZoomSDKInterop _zoomSDK;

    public MainForm() {
        InitializeComponent();
        InitializeZoomSDK();
    }

    private void InitializeZoomSDK() {
        _zoomSDK = new ZoomSDKInterop();

        // Subscribe to events
        _zoomSDK.SessionJoined += OnSessionJoined;
        _zoomSDK.PreviewVideoReceived += OnPreviewVideo;
        _zoomSDK.RemoteVideoReceived += OnRemoteVideo;

        _zoomSDK.Initialize();
    }

    private void OnPreviewVideo(object sender, VideoFrameEventArgs e) {
        // Must marshal to UI thread
        if (InvokeRequired) {
            BeginInvoke(new Action(() => OnPreviewVideo(sender, e)));
            return;
        }

        // Display bitmap in PictureBox
        _selfVideoPanel.Image?.Dispose();
        _selfVideoPanel.Image = e.Frame;
    }
}
```

### WinForms Flow Summary

```
C# Layer:
1. new ZoomSDKInterop() → creates C++/CLI ZoomSDKManager
2. Subscribe to events (SessionJoined, PreviewVideoReceived, etc.)
3. _zoomSDK.Initialize() → SDK init
4. _zoomSDK.JoinSession(...) → join
5. _zoomSDK.StartVideo() → start camera + preview

C++/CLI Layer:
1. Creates native SDK via CreateZoomVideoSDKObj()
2. Creates VideoPreviewHandler with gcroot<ZoomSDKManager^>
3. Starts Raw Data Pipe subscription
4. onRawDataFrameReceived → YUV→RGB → fires PreviewVideoReceived event

C# Layer (UI Thread):
1. OnPreviewVideo receives Bitmap
2. Checks InvokeRequired for thread safety
3. Sets PictureBox.Image = bitmap
```

### Sample Location
```
C:\tempsdk\videosdk-windows-dotnet-desktop-framework-quickstart\
  ├── ZoomVideoSDK.Wrapper\         # C++/CLI Bridge
  │   ├── ZoomSDKManager.h          # Managed class definition
  │   └── ZoomSDKManager.cpp        # Native ↔ Managed bridge
  │
  └── ZoomVideoSDK.WinForms\        # C# WinForms App
      ├── ZoomSDKInterop.cs         # High-level C# wrapper
      ├── MainForm.cs               # UI + event handlers
      └── Program.cs                # Entry point
```

---

## Option 3: WPF (C# + C++/CLI Wrapper)

**Same C++/CLI wrapper as WinForms**, but with additional WPF-specific handling.

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    C# WPF       │────►│  C# Interop     │────►│  C++/CLI Wrapper│────►│  Native C++ SDK │
│  (MainWindow)   │◄────│  (ZoomSDKInterop)│◄────│  (ZoomSDKManager)│◄────│  (videosdk.dll) │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
     BitmapSource        Bitmap→BitmapSource     gcroot<T^>              Callbacks
     Dispatcher          Conversion              YUV→RGB                 YUVRawDataI420
```

### Key Differences from WinForms

| Aspect | WinForms | WPF |
|--------|----------|-----|
| **Video Type** | `System.Drawing.Bitmap` | `System.Windows.Media.Imaging.BitmapSource` |
| **UI Thread** | `InvokeRequired` + `BeginInvoke` | `Dispatcher.CheckAccess()` + `Dispatcher.BeginInvoke` |
| **Image Control** | `PictureBox.Image` | `Image.Source` |
| **Extra Step** | None | Bitmap → BitmapSource conversion |

### Key Patterns

#### 1. WPF-Specific Event Args

```csharp
// WPF uses BitmapSource instead of Bitmap
public class VideoFrameEventArgs : EventArgs {
    public BitmapSource Frame { get; set; }  // WPF type
    public string UserId { get; set; }
}
```

#### 2. Bitmap → BitmapSource Conversion

```csharp
// ZoomSDKInterop.cs (WPF version)
private BitmapSource ConvertBitmapToBitmapSource(Bitmap bitmap) {
    if (bitmap == null) return null;

    using (var memory = new MemoryStream()) {
        bitmap.Save(memory, System.Drawing.Imaging.ImageFormat.Png);
        memory.Position = 0;

        var bitmapImage = new BitmapImage();
        bitmapImage.BeginInit();
        bitmapImage.StreamSource = memory;
        bitmapImage.CacheOption = BitmapCacheOption.OnLoad;
        bitmapImage.EndInit();
        bitmapImage.Freeze();  // Make thread-safe for WPF

        return bitmapImage;
    }
}

// Event handler bridges C++/CLI Bitmap to WPF BitmapSource
_sdkManager.PreviewVideoReceived += (sender, e) => {
    var wpfFrame = ConvertBitmapToBitmapSource(e.Frame);
    PreviewVideoReceived?.Invoke(this, new VideoFrameEventArgs(wpfFrame, "self"));
};
```

#### 3. WPF Dispatcher for UI Thread

```csharp
// MainWindow.xaml.cs
private void OnPreviewVideoReceived(object sender, VideoFrameEventArgs e) {
    // WPF uses Dispatcher instead of InvokeRequired
    if (!Dispatcher.CheckAccess()) {
        Dispatcher.BeginInvoke(new Action<object, VideoFrameEventArgs>(OnPreviewVideoReceived), sender, e);
        return;
    }

    // Frame throttling (~30fps)
    if (DateTime.Now - _lastPreviewVideoUpdate < _videoUpdateInterval) return;
    _lastPreviewVideoUpdate = DateTime.Now;

    if (e.Frame != null) {
        SelfVideoImage.Source = e.Frame;  // WPF Image control
    }
}
```

#### 4. Alternative: WriteableBitmap (Higher Performance)

For better performance, you can write directly to WriteableBitmap:

```csharp
private BitmapSource CreateErrorBitmapSource(int width, int height, string message) {
    var writeableBitmap = new WriteableBitmap(width, height, 96, 96, PixelFormats.Bgr24, null);
    writeableBitmap.Lock();

    unsafe {
        byte* backBuffer = (byte*)writeableBitmap.BackBuffer;
        int stride = writeableBitmap.BackBufferStride;

        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                byte* pixel = backBuffer + y * stride + x * 3;
                pixel[0] = 0;    // Blue
                pixel[1] = 0;    // Green
                pixel[2] = 255;  // Red
            }
        }
    }

    writeableBitmap.AddDirtyRect(new Int32Rect(0, 0, width, height));
    writeableBitmap.Unlock();
    writeableBitmap.Freeze();  // Thread-safe

    return writeableBitmap;
}
```

### WPF Flow Summary

```
Same as WinForms, with these differences:

C# WPF Interop Layer:
1. Receives Bitmap from C++/CLI wrapper
2. Converts Bitmap → BitmapSource (PNG stream or WriteableBitmap)
3. Calls Freeze() to make cross-thread safe
4. Fires WPF-compatible event

MainWindow (UI Thread):
1. OnPreviewVideoReceived receives BitmapSource
2. Checks Dispatcher.CheckAccess() for thread safety
3. Sets Image.Source = bitmapSource
```

### Sample Location
```
C:\tempsdk\videosdk-windows-dotnet-desktop-framework-quickstart\
  ├── ZoomVideoSDK.Wrapper\         # C++/CLI Bridge (shared with WinForms)
  │   ├── ZoomSDKManager.h
  │   └── ZoomSDKManager.cpp
  │
  └── ZoomVideoSDK.WPF\             # C# WPF App
      ├── ZoomSDKInterop.cs         # WPF-specific interop (BitmapSource)
      ├── MainWindow.xaml           # XAML layout
      ├── MainWindow.xaml.cs        # Code-behind with Dispatcher
      └── App.xaml                  # Application entry
```

---

## Decision Matrix

| If you need... | Use | Why |
|----------------|-----|-----|
| **Best performance** | Win32 | Canvas API, SDK renders directly |
| **C++ codebase** | Win32 | No interop overhead |
| **Existing WinForms app** | WinForms + C++/CLI | Natural integration |
| **Modern .NET UI** | WPF + C++/CLI | XAML, data binding |
| **Cross-platform .NET** | Consider Avalonia | WPF-like but cross-platform |

## C++/CLI Wrapper Patterns (For .NET Integration)

This section teaches **general C++/CLI wrapping patterns** applicable to ANY native C++ library.

### When to Use C++/CLI

| Scenario | Solution |
|----------|----------|
| Native C++ library → C# app | C++/CLI wrapper (this guide) |
| C library → C# app | P/Invoke (simpler, no wrapper needed) |
| COM library → C# app | COM Interop |
| .NET library → C++ app | Reverse P/Invoke or COM |

### Project Setup

1. **Create C++/CLI Class Library**:
   - Visual Studio → New Project → "CLR Class Library (.NET Framework)"
   - Or add `/clr` to existing C++ project

2. **Project Properties**:
   ```
   Configuration Properties → General:
   - Common Language Runtime Support: /clr
   - .NET Target Framework: v4.8

   C/C++ → General:
   - Additional Include Directories: path\to\native\sdk\include

   Linker → General:
   - Additional Library Directories: path\to\native\sdk\lib

   Linker → Input:
   - Additional Dependencies: native_sdk.lib
   ```

3. **File Structure**:
   ```
   MyWrapper/
   ├── MyWrapper.h         # Managed ref class definition
   ├── MyWrapper.cpp       # Implementation
   ├── NativeCallbacks.h   # Native callback classes with gcroot
   └── Stdafx.h            # Precompiled header
   ```

---

### Pattern 1: Basic Wrapper Structure

**Goal**: Expose native C++ class to C#

```cpp
// MyWrapper.h (C++/CLI)
#pragma once
#include <msclr\marshal_cppstd.h>  // For string conversion

using namespace System;
using namespace System::Runtime::InteropServices;

namespace MyLibraryWrapper {

    // Forward declare native types (hide from C#)
    class NativeClass;  // Don't #include native headers here!

    public ref class ManagedWrapper {
    private:
        NativeClass* m_pNative;  // Raw pointer to native object
        bool m_disposed;

    public:
        ManagedWrapper();
        ~ManagedWrapper();       // Destructor (IDisposable.Dispose)
        !ManagedWrapper();       // Finalizer (destructor fallback)

        // Managed methods that wrap native calls
        bool Initialize();
        void DoSomething(String^ param);
        String^ GetResult();
    };
}
```

```cpp
// MyWrapper.cpp
#include "stdafx.h"
#include "MyWrapper.h"
#include "native_sdk.h"  // Include native headers in .cpp only!

namespace MyLibraryWrapper {

    ManagedWrapper::ManagedWrapper() : m_pNative(nullptr), m_disposed(false) {
        m_pNative = new NativeClass();
    }

    ManagedWrapper::~ManagedWrapper() {
        this->!ManagedWrapper();  // Call finalizer
        m_disposed = true;
    }

    ManagedWrapper::!ManagedWrapper() {
        if (m_pNative) {
            delete m_pNative;
            m_pNative = nullptr;
        }
    }

    bool ManagedWrapper::Initialize() {
        if (!m_pNative) return false;
        return m_pNative->init() == 0;  // Native returns 0 for success
    }

    void ManagedWrapper::DoSomething(String^ param) {
        if (!m_pNative) return;

        // Convert managed String^ to native std::wstring
        std::wstring nativeParam = msclr::interop::marshal_as<std::wstring>(param);
        m_pNative->doSomething(nativeParam.c_str());
    }

    String^ ManagedWrapper::GetResult() {
        if (!m_pNative) return nullptr;

        // Convert native wchar_t* to managed String^
        const wchar_t* result = m_pNative->getResult();
        return result ? gcnew String(result) : nullptr;
    }
}
```

---

### Pattern 2: Opaque void* Pointers

**Goal**: Hide native types from managed headers (prevents header dependency leaks)

```cpp
// In .h file - use void* to hide native types
private:
    void* m_pNativeSDK;     // Actually INativeSDK*
    void* m_pNativeSession; // Actually INativeSession*

// In .cpp file - cast back to real types
bool ManagedWrapper::JoinSession() {
    INativeSDK* sdk = static_cast<INativeSDK*>(m_pNativeSDK);
    INativeSession* session = sdk->joinSession(...);
    m_pNativeSession = static_cast<void*>(session);
    return session != nullptr;
}
```

**Why**: Native SDK headers often have complex dependencies. Using `void*` means you only need to `#include` native headers in the `.cpp` file, not the `.h` file. This prevents compile errors in consuming C# projects.

---

### Pattern 3: gcroot<T^> for Native→Managed Callbacks

**Goal**: Native code needs to call back into managed code

```cpp
// NativeCallbacks.h
#pragma once
#include <vcclr.h>  // For gcroot

// Forward declare the managed class
namespace MyLibraryWrapper { ref class ManagedWrapper; }

// Native class that implements SDK callback interface
class NativeEventHandler : public INativeEventListener {
private:
    gcroot<MyLibraryWrapper::ManagedWrapper^> m_managed;  // GC-safe ref

public:
    NativeEventHandler(MyLibraryWrapper::ManagedWrapper^ wrapper)
        : m_managed(wrapper) {}

    // Native callback (called by SDK on background thread)
    void onEvent(int eventCode, const wchar_t* message) override {
        // Get managed reference (prevents GC during callback)
        MyLibraryWrapper::ManagedWrapper^ wrapper = m_managed;
        if (wrapper) {
            wrapper->FireManagedEvent(eventCode, gcnew String(message));
        }
    }

    void onDataReceived(const unsigned char* data, int length) override {
        MyLibraryWrapper::ManagedWrapper^ wrapper = m_managed;
        if (wrapper) {
            // Copy native data to managed array
            array<Byte>^ managedData = gcnew array<Byte>(length);
            Marshal::Copy(IntPtr((void*)data), managedData, 0, length);
            wrapper->FireDataEvent(managedData);
        }
    }
};
```

```cpp
// In ManagedWrapper.h - add events
public ref class ManagedWrapper {
public:
    // Managed events for C# consumption
    event EventHandler<EventArgs^>^ SomethingHappened;
    event EventHandler<DataEventArgs^>^ DataReceived;

internal:
    // Called by native callback handler
    void FireManagedEvent(int code, String^ message);
    void FireDataEvent(array<Byte>^ data);
};
```

**Critical**: `gcroot<T^>` prevents the .NET garbage collector from moving/collecting the managed object while native code holds a reference. Without it, callbacks will crash.

---

### Pattern 4: Destructor + Finalizer (IDisposable)

**Goal**: Guarantee native resource cleanup

```cpp
public ref class ManagedWrapper {
private:
    NativeClass* m_pNative;
    NativeEventHandler* m_pHandler;  // Must also be cleaned up
    bool m_disposed;

public:
    // Destructor - called by Dispose() or 'using' statement
    ~ManagedWrapper() {
        if (!m_disposed) {
            this->!ManagedWrapper();  // Call finalizer logic
            m_disposed = true;
            GC::SuppressFinalize(this);  // No need for finalizer now
        }
    }

    // Finalizer - called by GC if Dispose wasn't called
    !ManagedWrapper() {
        // Clean up in reverse order of creation
        if (m_pHandler) {
            delete m_pHandler;
            m_pHandler = nullptr;
        }
        if (m_pNative) {
            m_pNative->shutdown();  // SDK cleanup
            delete m_pNative;
            m_pNative = nullptr;
        }
    }
};
```

**C# Usage**:
```csharp
// Option 1: Explicit dispose
var wrapper = new ManagedWrapper();
try {
    wrapper.Initialize();
    // use wrapper...
} finally {
    wrapper.Dispose();  // Calls ~ManagedWrapper()
}

// Option 2: using statement (preferred)
using (var wrapper = new ManagedWrapper()) {
    wrapper.Initialize();
    // use wrapper...
}  // Dispose() called automatically
```

---

### Pattern 5: String Conversion

**Goal**: Convert between managed String^ and native strings

```cpp
#include <msclr\marshal_cppstd.h>

// Managed String^ → Native std::wstring
void SetName(String^ name) {
    std::wstring nativeName = msclr::interop::marshal_as<std::wstring>(name);
    m_pNative->setName(nativeName.c_str());
}

// Managed String^ → Native std::string (UTF-8)
void SetNameUtf8(String^ name) {
    std::string nativeName = msclr::interop::marshal_as<std::string>(name);
    m_pNative->setNameUtf8(nativeName.c_str());
}

// Native wchar_t* → Managed String^
String^ GetName() {
    const wchar_t* name = m_pNative->getName();
    return name ? gcnew String(name) : nullptr;
}

// Native char* (UTF-8) → Managed String^
String^ GetNameUtf8() {
    const char* name = m_pNative->getNameUtf8();
    return name ? gcnew String(name, 0, strlen(name), System::Text::Encoding::UTF8) : nullptr;
}
```

---

### Pattern 6: Array/Buffer Conversion

**Goal**: Pass binary data between managed and native code

```cpp
// Managed array → Native buffer
void SendData(array<Byte>^ data) {
    if (data == nullptr || data->Length == 0) return;

    // Pin the managed array (prevents GC from moving it)
    pin_ptr<Byte> pinned = &data[0];
    unsigned char* nativePtr = pinned;

    m_pNative->sendData(nativePtr, data->Length);
}
// pinned automatically unpins when out of scope

// Native buffer → Managed array
array<Byte>^ ReceiveData() {
    unsigned char* buffer = nullptr;
    int length = 0;

    m_pNative->receiveData(&buffer, &length);

    if (!buffer || length <= 0) return nullptr;

    array<Byte>^ result = gcnew array<Byte>(length);
    Marshal::Copy(IntPtr(buffer), result, 0, length);

    m_pNative->freeBuffer(buffer);  // SDK may require this
    return result;
}
```

---

### Pattern 7: Thread Marshaling (Native Thread → UI Thread)

**Goal**: Fire events safely when native callbacks occur on background threads

```cpp
// In native callback handler
void NativeEventHandler::onVideoFrame(YUVData* frame) {
    ManagedWrapper^ wrapper = m_managed;
   

... [Content truncated, total 37,341 chars] ...