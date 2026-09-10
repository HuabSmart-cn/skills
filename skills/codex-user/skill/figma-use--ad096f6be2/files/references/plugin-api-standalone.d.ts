// https://raw.githubusercontent.com/figma/plugin-typings/refs/heads/master/plugin-api-standalone.d.ts

/* plugin-typings are auto-generated. Do not update them directly. See developer-docs/ for instructions. */
/**
 * NOTE: This file is useful if you want to import specific types eg.
 * import type { SceneNode } from "@figma/plugin-typings/plugin-api-standalone"
 */
/**
 * @see https://developers.figma.com/docs/plugins/api/properties/figma-on
 */
declare type ArgFreeEventType =
  | 'selectionchange'
  | 'currentpagechange'
  | 'close'
  | 'timerstart'
  | 'timerstop'
  | 'timerpause'
  | 'timerresume'
  | 'timeradjust'
  | 'timerdone'
/**
 * @see https://developers.figma.com/docs/plugins/api/figma
 */
interface PluginAPI {
  /**
   * The version of the Figma API this plugin is running on, as defined in your `manifest.json` in the `"api"` field.
   */
  readonly apiVersion: '1.0.0'
  /**
   * The currently executing command from the `manifest.json` file. It is the command string in the `ManifestMenuItem` (more details in the [manifest guide](https://developers.figma.com/docs/plugins/manifest)). If the plugin does not have any menu item, this property is undefined.
   */
  readonly command: string
  /**
   * The current editor type this plugin is running in. See also [Setting editor type](https://developers.figma.com/docs/plugins/setting-editor-type).
   */
  readonly editorType: 'figma' | 'figjam' | 'dev' | 'slides' | 'buzz'
  /**
   * Return the context the plugin is current running in.
   *
   * - `default` - The plugin is running as a normal plugin.
   * - `textreview` - The plugin is running to provide text review functionality.
   * - `inspect` - The plugin is running in the Inspect panel in Dev Mode.
   * - `codegen` - The plugin is running in the Code section of the Inspect panel in Dev Mode.
   * - `linkpreview` - The plugin is generating a link preview for a [Dev resource](https://help.figma.com/hc/en-us/articles/15023124644247#Add_external_links_and_resources_for_developers) in Dev Mode.
   * - `auth` - The plugin is running to authenticate a user in Dev Mode.
   *
   * Caution: The `linkpreview` and `auth` modes are only available to partner and Figma-owned plugins.
   *
   * @remarks
   * Here’s a simplified example where you can create an if statement in a plugin that has one set of functionality when it is run in `Dev Mode`, and another set of functionality when run in Figma design:
   * ```ts title="Code sample to determine editorType and mode"
   * if (figma.editorType === "dev") {
   *   // Read the document and listen to API events
   *   if (figma.mode === "inspect") {
   *     // Running in inspect panel mode
   *   } else if (figma.mode === "codegen") {
   *     // Running in codegen mode
   *   }
   * } else if (figma.editorType === "figma") {
   *   // If the plugin is run in Figma design, edit the document
   *   if (figma.mode === 'textreview') {
   *     // Running in text review mode
   *   }
   * } else if (figma.editorType === "figjam") {
   *   // Do FigJam only operations
   *   if (figma.mode === 'textreview') {
   *     // Running in text review mode
   *   }
   * }
   * ```
   */
  readonly mode: 'default' | 'textreview' | 'inspect' | 'codegen' | 'linkpreview' | 'auth'
  /**
   * The value specified in the `manifest.json` "id" field. This only exists for Plugins.
   */
  readonly pluginId?: string
  /**
   * Similar to `figma.pluginId` but for widgets. The value specified in the `manifest.json` "id" field. This only exists for Widgets.
   */
  readonly widgetId?: string
  /**
   * The file key of the current file this plugin is running on.
   * **Only [private plugins](https://help.figma.com/hc/en-us/articles/4404228629655-Create-private-organization-plugins) and Figma-owned resources (such as the Jira and Asana widgets) have access to this.**
   * To enable this behavior, you need to specify `enablePrivatePluginApi` in your `manifest.json`.
   */
  readonly fileKey: string | undefined
  /**
   * When enabled, causes all node properties and methods to skip over invisible nodes (and their descendants) inside {@link InstanceNode | instances}.
   * This makes operations like document traversal much faster.
   *
   * Note: Defaults to true in Figma Dev Mode and false in Figma and FigJam
   *
   * @remarks
   *
   * Accessing and modifying invisible nodes and their descendants inside instances can be slow with the plugin API.
   * This is especially true in large documents with tens of thousands of nodes where a call to {@link ChildrenMixin.findAll} might come across many of these invisible instance children.
   *
   * If your plugin does not need access to these nodes, we recommend setting `figma.skipInvisibleInstanceChildren = true` as that often makes document traversal significantly faster.
   *
   * When this flag is enabled, it will not be possible to access invisible nodes (and their descendants) inside instances. This has the following effects:
   *
   * - {@link ChildrenMixin.children} and methods such as {@link ChildrenMixin.findAll} will exclude these nodes.
   * - {@link PluginAPI.getNodeByIdAsync} will return a promise containing null.
   * - {@link PluginAPI.getNodeById} will return null.
   * - Accessing a property on an existing node object for an invisible node will throw an error.
   *
   * For example, suppose that a portion of the document tree looks like this:
   *
   * Frame (visible) → Instance (visible) → Frame (invisible) → Text (visible)
   *
   * The last two frame and text nodes cannot be accessed after setting `figma.skipInvisibleInstanceChildren = true`.
   *
   * The benefit of enabling this flag is that document traversal methods, {@link ChildrenMixin.findAll} and {@link ChildrenMixin.findOne}, can be up to several times faster in large documents that have invisible instance children.
   * {@link ChildrenMixin.findAllWithCriteria} can be up to hundreds of times faster in large documents.
   */
  skipInvisibleInstanceChildren: boolean
  /**
   * Note: This API is only available in FigJam
   *
   * This property contains methods used to read, set, and modify the built in FigJam timer.
   *
   * Read more in the [timer section](https://developers.figma.com/docs/plugins/api/figma-timer).
   */
  readonly timer?: TimerAPI
  /**
   * This property contains methods used to read and set the viewport, the user-visible area of the current page.
   *
   * Read more in the [viewport section](https://developers.figma.com/docs/plugins/api/figma-viewport).
   */
  readonly viewport: ViewportAPI
  /**
   * Note: `currentuser` must be specified in the permissions array in `manifest.json` to access this property.
   *
   * This property contains details about the current user.
   */
  readonly currentUser: User | null
  /**
   * Note: This API is only available in FigJam.
   *
   * `activeusers` must be specified in the permissions array in `manifest.json` to access this property.
   *
   * This property contains details about the active users in the file. `figma.activeUsers[0]` will match `figma.currentUser` for the `id`, `name`, `photoUrl`, `color`, and `sessionId` properties.
   */
  readonly activeUsers: ActiveUser[]
  /**
   * Note: `textreview` must be specified in the capabilities array in `manifest.json` to access this property.
   *
   * This property contains methods that enable text review features in your plugin.
   */
  readonly textreview?: TextReviewAPI
  /**
   * This property contains methods used to integrate with the Dev Mode codegen functionality.
   *
   * Read more in the [codegen section](https://developers.figma.com/docs/plugins/api/figma-codegen).
   */
  readonly codegen: CodegenAPI
  /**
   * This property contains methods used to integrate with the Figma for VS Code extension. If `undefined`, the plugin is not running in VS Code.
   *
   * Read more in [Dev Mode plugins in Visual Studio Code](https://developers.figma.com/docs/plugins/working-in-dev-mode#dev-mode-plugins-in-visual-studio-code)
   */
  readonly vscode?: VSCodeAPI
  /**
   * Caution: This is a private API only available to [Figma partners](https://www.figma.com/partners/)
   */
  readonly devResources?: DevResourcesAPI
  /**
   * Note: `payments` must be specified in the permissions array in `manifest.json` to access this property.
   *
   * This property contains methods for plugins that require payment.
   */
  readonly payments?: PaymentsAPI
  /**
   * Closes the plugin. You should always call this function once your plugin is done running. When called, any UI that's open will be closed and any `setTimeout` or `setInterval` timers will be cancelled.
   *
   * @param message - Optional -- display a visual bell toast with the message after the plugin closes.
   *
   * @remarks
   *
   * Calling `figma.closePlugin()` disables callbacks and Figma APIs. It does not, however, abort the plugin. Any lines of Javascript after this call will also run. For example, consider the following plugin that expects the user to have one layer selected:
   *
   * ```ts title="Simple closePlugin"
   * if (figma.currentPage.selection.length !== 1) {
   *   figma.closePlugin()
   * }
   * figma.currentPage.selection[0].opacity = 0.5
   * ```
   *
   * This will not work. The last line will still run, but will throw an exception because access to `figma.currentPage` has been disabled. As such, it is not recommended to run any code after calling `figma.closePlugin()`.
   *
   * A simple way to easily exit your plugin is to wrap your plugin in a function, instead of running code at the top-level, and always follow `figma.closePlugin()` with a `return` statement:
   *
   * ```ts title="Early return"
   * function main() {
   *   if (figma.currentPage.selection.length !== 1) {
   *     figma.closePlugin()
   *     return
   *   }
   *   figma.currentPage.selection[0].opacity = 0.5
   * }
   * main()
   * ```
   *
   * It's good practice to have all input validation done at the start of the plugin. However, there may be cases where the plugin may need to close after a chain of multiple function calls. If you expect to have to close the plugin deep within your code, but don't want to necessarily want the user to see an error, the example above will not be sufficient.
   *
   * One alternative is to use a top-level try-catch statement. However, you will need to be responsible for making sure that there are no usages of try-catch between the top-level try-catch and the call to `figma.closePlugin()`, or to pass along the close command if necessary. Example:
   *
   * ```ts title="Top-level try-catch"
   * const CLOSE_PLUGIN_MSG = "_CLOSE_PLUGIN_"
   * function someNestedFunctionCallThatClosesThePlugin() {
   *   throw CLOSE_PLUGIN_MSG
   * }
   *
   * function main() {
   *   someNestedFunctionCallThatClosesThePlugin()
   * }
   *
   * try {
   *   main()
   * } catch (e) {
   *   if (e === CLOSE_PLUGIN_MSG) {
   *     figma.closePlugin()
   *   } else {
   *     // >> DO NOT LEAVE THIS OUT <<
   *     // If we caught any other kind of exception,
   *     // it's a real error and should be passed along.
   *     throw e
   *   }
   * }
   * ```
   */
  closePlugin(message?: string): void
  /**
   * Shows a notification on the bottom of the screen.
   *
   * @param message - The message to show. It is limited to 100 characters. Longer messages will be truncated.
   * @param options - An optional argument with the following optional parameters:
   *
   * ```ts
   * interface NotificationOptions {
   *   timeout?: number;
   *   error?: boolean;
   *   onDequeue?: (reason: NotifyDequeueReason) => void
   *   button?: {
   *     text: string
   *     action: () => boolean | void
   *   }
   * }
   * ```
   *
   * - `timeout`: How long the notification stays up in milliseconds before closing. Defaults to 3 seconds when not specified. Set the timeout to `Infinity` to make the notification show indefinitely until the plugin is closed.
   * - `error`: If true, display the notification as an error message, with a different color.
   * - `onDequeue`: A function that will run when the notification is dequeued. This can happen due to the timeout being reached, the notification being dismissed by the user or Figma, or the user clicking the notification's `button`.
   *   - The function is passed a `NotifyDequeueReason`, which is defined as the following:
   * ```ts
   *  type NotifyDequeueReason = 'timeout' | 'dismiss' | 'action_button_click'
   *  ```
   * - `button`: An object representing an action button that will be added to the notification.
   *    - `text`: The message to display on the action button.
   *    - `action`: The function to execute when the user clicks the button. If this function returns `false`, the message will remain when the button is clicked. Otherwise, clicking the action button dismisses the notify message.
   *
   * @remarks
   *
   * The `notify` API is a convenient way to show a message to the user. These messages can be queued.
   *
   * If the message includes a custom action button, it will be closed automatically when the plugin closes.
   *
   * Calling `figma.notify` returns a `NotificationHandler` object. This object contains a single `handler.cancel()` method that can be used to remove the notification before it times out by itself. This is useful if the notification becomes no longer relevant.
   *
   * ```ts
   * interface NotificationHandler {
   *   cancel: () => void
   * }
   * ```
   *
   * An alternative way to show a message to the user is to pass a message to the {@link PluginAPI.closePlugin} function.
   */
  notify(message: string, options?: NotificationOptions): NotificationHandler
  /**
   * Commits actions to undo history. This does not trigger an undo.
   *
   * @remarks
   *
   * By default, plugin actions are not committed to undo history. Call `figma.commitUndo()` so that triggered
   * undos can revert a subset of plugin actions.
   *
   * For example, after running the following plugin code, the first triggered undo will undo both the rectangle and the ellipse:
   * ```ts
   * figma.createRectangle();
   * figma.createEllipse();
   * figma.closePlugin();
   * ```
   * Whereas if we call `commitUndo()` in our plugin, the first triggered undo will only undo the ellipse:
   * ```ts
   * figma.createRectangle();
   * figma.commitUndo();
   * figma.createEllipse();
   * figma.closePlugin();
   * ```
   */
  commitUndo(): void
  /**
   * Triggers an undo action. Reverts to the last `commitUndo()` state.
   */
  triggerUndo(): void
  /**
   * Saves a new version of the file and adds it to the version history of the file. Returns the new version id.
   * @param title - The title of the version. This must be a non-empty string.
   * @param description - An optional argument to describe the version.
   *
   * Calling `saveVersionHistoryAsync` returns a promise that resolves to `null` or an instance of `VersionHistoryResult`:
   *
   * ```ts
   * interface VersionHistoryResult {
   *   id: string
   * }
   * ```
   *
   * - `id`: The version id of this newly saved version.
   *
   * @remarks
   *
   * It is not guaranteed that all changes made before this method is used will be saved to version history.
   * For example,
   *  ```ts title="Changes may not all be saved"
   *  async function example() {
   *    await figma.createRectangle();
   *    await figma.saveVersionHistoryAsync('v1');
   *    figma.closePlugin();
   *  }
   *  example().catch((e) => figma.closePluginWithFailure(e))
   *  ```
   * The newly created rectangle may not be included in the v1 version. As a work around, you can wait before calling `saveVersionHistoryAsync()`. For example,
   *  ```ts title="Wait to save"
   *  async function example() {
   *    await figma.createRectangle();
   *    await new Promise(r => setTimeout(r, 1000)); // wait for 1 second
   *    await figma.saveVersionHistoryAsync('v1');
   *    figma.closePlugin();
   *  }
   * ```
   * Typically, manual changes that precede the execution of `saveVersionHistoryAsync()` will be included. If you want to use `saveVersionHistoryAsync()` before the plugin makes
   * additional changes, make sure to use the method with an async/await or a Promise.
   */
  saveVersionHistoryAsync(title: string, description?: string): Promise<VersionHistoryResult>
  /**
   * Open a url in a new tab.
   *
   * @remarks
   *
   * In the VS Code Extension, this API is required to open a url in the browser. Read more in [Dev Mode plugins in Visual Studio Code](https://developers.figma.com/docs/plugins/working-in-dev-mode#dev-mode-plugins-in-visual-studio-code).
   */
  openExternal(url: string): void
  /**
   * Enables you to render UI to interact with the user, or simply to access browser APIs. This function creates a modal dialog with an `<iframe>` containing the HTML markup in the `html` argument.
   *
   * @param html - The HTML to insert into the iframe. You can pass in the HTML code as a string here, but this will often be the global value [`__html__`](https://developers.figma.com/docs/plugins/api/global-objects#html).
   * @param options - An object that may contain the following optional parameters:
   * - `visible`: Whether the UI starts out displayed to the user. Defaults to `true`. You can use `figma.ui.show()` and `figma.ui.hide()` to change the visibility later.
   * - `width`: The width of the UI. Defaults to 300. Minimum is 70. Can be changed later using `figma.ui.resize(width, height)`
   * - `height`: The height of the UI. Defaults to 200. Minimum is 0. Can be changed later using `figma.ui.resize(width, height)`
   * - `title`: The title of the UI window. Defaults to the plugin name.
   * - `position`: The position of the UI window. Defaults to the last position of the iframe or the center of the viewport. If specified, expects an X/Y coordinate in the canvas space (i.e matches x/y values returned by `<PluginNode>.x` and `<PluginNode>.y`)
   * - `themeColors`: Defaults to `false`. When enabled, CSS variables will be added to the plugin iframe to allow [support for light and dark themes](https://developers.figma.com/docs/plugins/css-variables).
   *
   * Note: If the position specified is outside of the user's viewport, the iframe will be moved so that it remains in the user's viewport.
   *
   * @remarks
   *
   * The easiest way to use this API is to load the HTML file defined in the manifest. This enables writing a separate HTML file which can be accessed through the [`__html__`](https://developers.figma.com/docs/plugins/api/global-objects#html) global variable.
   *
   * If the `<iframe>` UI is already showing when this function is called, the previous UI will be closed before the new one is displayed.
   *
   * ## Usage Examples
   *
   * ```js title="Example usage"
   * figma.showUI(
   *   "<b>Hello from Figma</b>",
   *   { width: 400, height: 200, title: "My title" }
   * )
   *
   * figma.showUI(
   *   "<b>Hello from Figma</b>",
   *   { width: 400, height: 200, title: "My title", position: { x: 100, y: 100 } }
   * )
   *
   * figma.showUI(__html__)
   * ```
   */
  showUI(html: string, options?: ShowUIOptions): void
  /**
   * This property contains methods used to modify and communicate with the UI created via `figma.showUI(...)`.
   *
   * Read more in the [UI section](https://developers.figma.com/docs/plugins/api/figma-ui).
   */
  readonly ui: UIAPI
  /**
   * This property contains convenience functions for common operations.
   *
   * Read more in the [util section](https://developers.figma.com/docs/plugins/api/figma-util).
   */
  readonly util: UtilAPI
  /**
   * This property contains constants that can be accessed by the plugin API.
   *
   * Read more in the [constants section](https://developers.figma.com/docs/plugins/api/figma-constants).
   */
  readonly constants: ConstantsAPI
  /**
   * This property contains methods to store persistent data on the user's local machine.
   *
   * Read more in the [client storage section](https://developers.figma.com/docs/plugins/api/figma-clientStorage).
   */
  readonly clientStorage: ClientStorageAPI
  /**
   * This property contains methods to handle user inputs when a plugin is launched in query mode. See [Accepting Parameters as Input](https://developers.figma.com/docs/plugins/plugin-parameters) for more details.
   */
  readonly parameters: ParametersAPI
  /**
   * Finds a node by its id in the current document. Every node has an `id` property, which is unique within the document. If the id is invalid, or the node cannot be found (e.g. removed), returns a promise containing null.
   */
  getNodeByIdAsync(id: string): Promise<BaseNode | null>
  /**
   * @deprecated Use {@link PluginAPI.getNodeByIdAsync} instead. This function will throw an exception if the plugin manifest contains `"documentAccess": "dynamic-page"`.
   *
   * Finds a node by its id in the current document. Every node has an `id` property, which is unique within the document. If the id is invalid, or the node cannot be found (e.g. removed), returns null.
   */
  getNodeById(id: string): BaseNode | null
  /**
   * Finds a style by its id in the current document. If not found, returns a promise containing null.
   */
  getStyleByIdAsync(id: string): Promise<BaseStyle | null>
  /**
   * @deprecated Use {@link PluginAPI.getStyleByIdAsync} instead. This function will throw an exception if the plugin manifest contains `"documentAccess": "dynamic-page"`.
   *
   * Finds a style by its id in the current document. If not found, returns null.
   */
  getStyleById(id: string): BaseStyle | null
  /**
   * This property contains methods to work with Variables and Variable Collections within Figma.
   *
   * */
  readonly variables: VariablesAPI
  /** This property contains methods to work with assets residing in a team library. */
  readonly teamLibrary: TeamLibraryAPI
  /**
   * This property contains methods to work with annotations.
   *
   */
  readonly annotations: AnnotationsAPI
  /**
   *
   * This API is only available in Buzz.
   *
   * This property contains methods to work in Buzz.
   *
   */
  readonly buzz: BuzzAPI
  /**
   * The root of the entire Figma document. This node is used to access other pages. Each child is a {@link PageNode}.
   */
  readonly root: DocumentNode
  /**
   * The page that the user currently viewing. You can set this value to a {@link PageNode} to switch pages.
   *
   * * If the manifest contains`"documentAccess": "dynamic-page"`, this property is read-only. Use {@link PluginAPI.setCurrentPageAsync} to update the value.
   */
  currentPage: PageNode
  /**
   * Switch the active page to the specified {@link PageNode}.
   */
  setCurrentPageAsync(page: PageNode): Promise<void>
  /**
   * Registers an callback that will be called when an event happens in the editor. Current supported events are:
   * - The selection on the current page changed.
   * - The current page changed.
   * - The document has changed.
   * - An object from outside Figma is dropped onto the canvas
   * - The plugin has started running.
   * - The plugin closed.
   * - The plugin has started running.
   * - The timer has started running.
   * - The timer has paused.
   * - The timer has stopped.
   * - The timer is done.
   * - The timer has resumed.
   *
   *
   * @param type - A string identifying the type of event that the callback will be called on.
   *
   * This is either an `ArgFreeEventType`, `run`, `drop`, or `documentchange`. The `run` event callback will be passed a `RunEvent`. The `drop` event callback will be passed a `DropEvent`. The `documentchange` event callback will be passed a `DocumentChangeEvent`.
   *
   * ```ts
   * type ArgFreeEventType =
   *   "selectionchange" |
   *   "currentpagechange" |
   *   "close" |
   *   "timerstart" |
   *   "timerstop" |
   *   "timerpause" |
   *   "timerresume" |
   *   "timeradjust" |
   *   "timerdone"
   * ```
   *
   * @param callback - A function that will be called when the event happens.
   * If `type` is 'run', then this function will be passed a `RunEvent`.
   * If `type` is 'drop', then this function will be passed a `DropEvent`.
   * If `type` is 'documentchange', then this function will be passed a `DocumentChangeEvent`.
   *
   * Otherwise nothing will be passed in.
   *
   * @remarks
   *
   * This API tries to match Node.js conventions around similar `.on` APIs.
   *
   * It's important to understand that the `.on` API runs the callbacks **asynchronously**. For example:
   *
   * ```ts
   * figma.on("selectionchange", () => { console.log("changed") })
   * console.log("before")
   * figma.currentPage.selection = []
   * console.log("after")
   *
   * // Output:
   * // "before"
   * // "after"
   * // "changed"
   * ```
   *
   * The asynchronous nature of these APIs have a few other implications.
   *
   * The callback will not necessarily be called each time the event happens. For example, this will only trigger the event once:
   *
   * ```ts
 

... [Content truncated, total 455,369 chars] ...