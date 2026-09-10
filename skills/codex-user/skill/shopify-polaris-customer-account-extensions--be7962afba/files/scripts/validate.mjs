#!/usr/bin/env node

// src/agent-skills/scripts/validate_components.ts
import { readFileSync } from "fs";
import { parseArgs } from "util";

// src/types/api-types.ts
var Visibility = {
  PUBLIC: "public",
  EARLY_ACCESS: "earlyAccess",
  INTERNAL: "internal"
};
var APICategory = {
  GRAPHQL: "graphql",
  FUNCTIONS: "functions",
  FUNCTION_GRAPHQL: "function-graphql",
  // GraphQL schemas for Function input queries
  UI_FRAMEWORK: "ui-framework",
  THEME: "theme",
  CONFIGURATION: "configuration",
  EXECUTION: "execution",
  GUIDANCE: "guidance"
  // Procedural topics (onboarding, review checklists) — hand-maintained, no validation/search
};

// src/types/api-mapping.ts
function defineApis(apis) {
  return Object.fromEntries(
    Object.entries(apis).map(([name, config]) => [name, { name, ...config }])
  );
}
var SHOPIFY_APIS = defineApis({
  "use-shopify-cli": {
    displayName: "Use Shopify CLI",
    description: "Choose when the user needs **Shopify CLI** to run or fix something now: validate app or extension config on disk (`shopify.app.toml`, `shopify.app.<name>.toml`, `shopify.extension.toml`); run or troubleshoot store workflows (`shopify store auth`, `shopify store execute`); inventory or product changes by handle, SKU, or location name; or CLI setup, auth, upgrade issues. Emphasize **commands and operational steps**, not only authoring GraphQL. Skip for API-only understanding or codegen with no CLI execution. Examples: validate configuration before deploy; run an existing query via CLI; list products; missing `shopify store execute`.",
    category: APICategory.EXECUTION,
    visibility: Visibility.PUBLIC,
    searchable: false
  },
  ucp: {
    displayName: "UCP CLI",
    description: 'Use when the user wants to use the UCP CLI to find, compare, buy, or track products from online merchants, or to set up and troubleshoot the local UCP profile required for merchant-scoped operations. Covers global catalog search ("find me X under $Y"), named-merchant transactions ("buy this from Z.com"), order tracking, `ucp profile init`, `ucp doctor`, carts, checkout, orders, and UCP setup/help. Falls back to merchant-hosted handoff when direct in-protocol checkout isn\'t available.',
    category: APICategory.EXECUTION,
    visibility: Visibility.PUBLIC,
    searchable: false,
    skillName: "ucp",
    compatibility: "Requires UCP CLI",
    frontmatterExtras: { requires_bin: "ucp", command: "ucp" }
  },
  admin: {
    displayName: "Admin API",
    description: "Write or explain **Admin GraphQL** queries and mutations for apps and integrations that extend the Shopify admin. Use when the user wants to **understand, design, or generate** the operation itself\u2014even before deciding how to run it. Do **not** choose `admin` first for **app or extension config validation** \u2014use **`use-shopify-cli`**. Do **not** choose `admin` first to **execute** Admin GraphQL **now via Shopify CLI** or for CLI setup/troubleshooting on store workflows\u2014use **`use-shopify-cli`** (store auth/execute, handle/SKU/location lookups, inventory changes).",
    category: APICategory.GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "admin" },
    validation: true,
    exampleVectorStoreQuery: {
      query: "productCreate mutation",
      context: "creating a product"
    }
  },
  "storefront-graphql": {
    displayName: "Storefront GraphQL API",
    description: "Use for custom storefronts requiring direct GraphQL queries/mutations for data fetching and cart operations. Choose this when you need full control over data fetching and rendering your own UI. NOT for Web Components - if the prompt mentions HTML tags like <shopify-store>, <shopify-cart>, use storefront-web-components instead.",
    category: APICategory.GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "storefront" },
    validation: true,
    exampleVectorStoreQuery: {
      query: "predictiveSearch query",
      context: "storefront search"
    }
  },
  partner: {
    displayName: "Partner API",
    description: "The Partner API lets you programmatically access data about your Partner Dashboard, including your apps, themes, and affiliate referrals.",
    category: APICategory.GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "partner" },
    validation: true,
    exampleVectorStoreQuery: {
      query: "transactions query",
      context: "partner transaction history"
    }
  },
  customer: {
    displayName: "Customer Account API",
    description: "The Customer Account API allows customers to access their own data including orders, payment methods, and addresses.",
    category: APICategory.GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "customer" },
    validation: true,
    exampleVectorStoreQuery: {
      query: "customer orders query",
      context: "customer order history"
    }
  },
  "payments-apps": {
    displayName: "Payments Apps API",
    description: "The Payments Apps API enables payment providers to integrate their payment solutions with Shopify's checkout.",
    category: APICategory.GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "payments_apps" },
    validation: true,
    exampleVectorStoreQuery: {
      query: "paymentSessionPending mutation",
      context: "pending a payment session"
    }
  },
  functions: {
    displayName: "Shopify Functions",
    description: "Shopify Functions allow developers to customize the backend logic that powers parts of Shopify. Available APIs: Discount, Cart and Checkout Validation, Cart Transform, Pickup Point Delivery Option Generator, Delivery Customization, Fulfillment Constraints, Local Pickup Delivery Option Generator, Order Routing Location Rule, Payment Customization",
    category: APICategory.FUNCTIONS,
    visibility: Visibility.PUBLIC,
    validation: true,
    exampleVectorStoreQuery: {
      query: "cart transform function input query",
      context: "cart transform function inputs"
    }
  },
  // Function-specific GraphQL APIs for input query validation
  functions_cart_checkout_validation: {
    displayName: "Cart Checkout Validation Function",
    description: "GraphQL schema for Cart and Checkout Validation Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: {
      shopifyDevPrefix: "functions_cart_checkout_validation_schema"
    }
  },
  functions_cart_transform: {
    displayName: "Cart Transform Function",
    description: "GraphQL schema for Cart Transform Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "functions_cart_transform_schema" }
  },
  functions_delivery_customization: {
    displayName: "Delivery Customization Function",
    description: "GraphQL schema for Delivery Customization Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: {
      shopifyDevPrefix: "functions_delivery_customization_schema"
    }
  },
  functions_discount: {
    displayName: "Discount Function",
    description: "GraphQL schema for Discount Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "functions_discount_schema" }
  },
  functions_discounts_allocator: {
    displayName: "Discounts Allocator Function",
    description: "GraphQL schema for Discounts Allocator Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "functions_discounts_allocator_schema" }
  },
  functions_fulfillment_constraints: {
    displayName: "Fulfillment Constraints Function",
    description: "GraphQL schema for Fulfillment Constraints Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: {
      shopifyDevPrefix: "functions_fulfillment_constraints_schema"
    }
  },
  functions_local_pickup_delivery_option_generator: {
    displayName: "Local Pickup Delivery Option Generator Function",
    description: "GraphQL schema for Local Pickup Delivery Option Generator Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: {
      shopifyDevPrefix: "functions_local_pickup_delivery_option_generator_schema"
    }
  },
  functions_order_discounts: {
    displayName: "Order Discounts Function",
    description: "GraphQL schema for Order Discounts Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "functions_order_discounts_schema" }
  },
  functions_order_routing_location_rule: {
    displayName: "Order Routing Location Rule Function",
    description: "GraphQL schema for Order Routing Location Rule Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: {
      shopifyDevPrefix: "functions_order_routing_location_rule_schema"
    }
  },
  functions_payment_customization: {
    displayName: "Payment Customization Function",
    description: "GraphQL schema for Payment Customization Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: {
      shopifyDevPrefix: "functions_payment_customization_schema"
    }
  },
  functions_pickup_point_delivery_option_generator: {
    displayName: "Pickup Point Delivery Option Generator Function",
    description: "GraphQL schema for Pickup Point Delivery Option Generator Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: {
      shopifyDevPrefix: "functions_pickup_point_delivery_option_generator_schema"
    }
  },
  functions_product_discounts: {
    displayName: "Product Discounts Function",
    description: "GraphQL schema for Product Discounts Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "functions_product_discounts_schema" }
  },
  functions_shipping_discounts: {
    displayName: "Shipping Discounts Function",
    description: "GraphQL schema for Shipping Discounts Function input queries",
    category: APICategory.FUNCTION_GRAPHQL,
    visibility: Visibility.PUBLIC,
    schemaSource: { shopifyDevPrefix: "functions_shipping_discounts_schema" }
  },
  "polaris-app-home": {
    displayName: "Polaris App Home",
    description: "Build your app's primary user interface embedded in the Shopify admin. If the prompt just mentions `Polaris` and you can't tell based off of the context what API they meant, assume they meant this API.",
    category: APICategory.UI_FRAMEWORK,
    publicPackages: ["@shopify/polaris-types", "@shopify/app-bridge-types"],
    visibility: Visibility.PUBLIC,
    validation: true,
    exampleVectorStoreQuery: {
      query: "s-form",
      context: "form in app home"
    }
  },
  "polaris-admin-extensions": {
    displayName: "Polaris Admin Extensions",
    description: `Add custom actions and blocks from your app at contextually relevant spots throughout the Shopify Admin. Admin UI Extensions also supports scaffolding new adminextensions using Shopify CLI commands.`,
    category: APICategory.UI_FRAMEWORK,
    publicPackages: ["@shopify/ui-extensions"],
    extensionSurfaceName: "admin",
    extensionTypeName: "Admin Extensions",
    extensionSearchContext: "admin UI extensions",
    visibility: Visibility.PUBLIC,
    validation: true,
    exampleVectorStoreQuery: {
      query: "admin.product-details.block.render",
      context: "admin extension target for product details blocks"
    },
    exampleExtensionTarget: "admin.product-details.block.render"
  },
  "polaris-checkout-extensions": {
    displayName: "Polaris Checkout Extensions",
    description: `Build custom functionality that merchants can install at defined points in the checkout flow, including product information, shipping, payment, order summary, and Shop Pay. Checkout UI Extensions also supports scaffolding new checkout extensions using Shopify CLI commands.`,
    category: APICategory.UI_FRAMEWORK,
    publicPackages: ["@shopify/ui-extensions"],
    extensionSurfaceName: "checkout",
    extensionTypeName: "Checkout Extensions",
    extensionSearchContext: "checkout UI extensions",
    visibility: Visibility.PUBLIC,
    validation: true,
    exampleVectorStoreQuery: {
      query: "s-button checkout",
      context: "checkout button"
    },
    exampleExtensionTarget: "purchase.checkout.block.render"
  },
  "polaris-customer-account-extensions": {
    displayName: "Polaris Customer Account Extensions",
    description: `Build custom functionality that merchants can install at defined points on the Order index, Order status, and Profile pages in customer accounts. Customer Account UI Extensions also supports scaffolding new customer account extensions using Shopify CLI commands.`,
    category: APICategory.UI_FRAMEWORK,
    publicPackages: ["@shopify/ui-extensions"],
    extensionSurfaceName: "customer-account",
    extensionTypeName: "Customer Account Extensions",
    extensionSearchContext: "customer account UI extensions",
    visibility: Visibility.PUBLIC,
    validation: true,
    exampleVectorStoreQuery: {
      query: "s-card customer-account",
      context: "customer account card"
    },
    exampleExtensionTarget: "customer-account.order-status.block.render"
  },
  "pos-ui": {
    displayName: "POS UI",
    description: `Build retail point-of-sale applications using Shopify's POS UI components. These components provide a consistent and familiar interface for POS applications. POS UI Extensions also supports scaffolding new POS extensions using Shopify CLI commands. Keywords: POS, Retail, smart grid`,
    category: APICategory.UI_FRAMEWORK,
    publicPackages: ["@shopify/ui-extensions"],
    extensionSurfaceName: "point-of-sale",
    extensionTypeName: "POS UI Extensions",
    extensionSearchContext: "POS UI extensions",
    visibility: Visibility.PUBLIC,
    validation: true,
    exampleVectorStoreQuery: {
      query: "pos.home.tile.render",
      context: "POS home tile extension target"
    },
    exampleExtensionTarget: "pos.customer-details.block.render"
  },
  hydrogen: {
    displayName: "Hydrogen",
    description: "Hydrogen storefront implementation cookbooks. Some of the available recipes are: B2B Commerce, Bundles, Combined Listings, Custom Cart Method, Dynamic Content with Metaobjects, Express Server, Google Tag Manager Integration, Infinite Scroll, Legacy Customer Account Flow, Markets, Partytown + Google Tag Manager, Subscriptions, Third-party API Queries and Caching. MANDATORY: Use this API for ANY Hydrogen storefront question - do NOT use Storefront GraphQL when 'Hydrogen' is mentioned.",
    category: APICategory.UI_FRAMEWORK,
    publicPackages: ["@shopify/hydrogen"],
    visibility: Visibility.PUBLIC,
    validation: true,
    exampleVectorStoreQuery: {
      query: "CartForm component",
      context: "cart UI"
    }
  },
  "storefront-web-components": {
    displayName: "Storefront Web Components",
    description: "HTML-first web components for building storefronts WITHOUT GraphQL. Choose when prompts mention: Web Components, HTML tags (<shopify-store>, <shopify-context>, <shopify-cart>, <shopify-variant-selector>, <shopify-money>), native <dialog>, 'HTML-only', 'without JavaScript', or 'no GraphQL'. Components handle data fetching and state internally.",
    category: APICategory.UI_FRAMEWORK,
    featureFlag: "storefrontWebComponentsEnabled",
    //TODO: Need to find the appropriate packages for Storefront Web Components.
    // Docs has <script src="https://cdn.shopify.com/storefront/web-components.js"></script> and not a npm package
    publicPackages: ["@shopify/polaris-types", "@shopify/app-bridge-types"],
    visibility: Visibility.EARLY_ACCESS,
    validation: true,
    exampleVectorStoreQuery: {
      query: "shopify-cart",
      context: "cart web component"
    }
  },
  liquid: {
    displayName: "Liquid",
    description: "Liquid is an open-source templating language created by Shopify. It is the backbone of Shopify themes and is used to load dynamic content on storefronts. Keywords: liquid, theme, shopify-theme, liquid-component, liquid-block, liquid-section, liquid-snippet, liquid-schemas, shopify-theme-schemas",
    category: APICategory.THEME,
    visibility: Visibility.PUBLIC,
    schemaSource: { npmPackage: "@shopify/theme-check-common" },
    validation: true,
    exampleVectorStoreQuery: {
      query: "product metafields",
      context: "product metafield access in a theme"
    }
  },
  "custom-data": {
    displayName: "Custom Data",
    description: "MUST be used first when prompts mention Metafields or Metaobjects. Use Metafields and Metaobjects to model and store custom data for your app. Metafields extend built-in Shopify data types like products or customers, Metaobjects are custom data types that can be used to store bespoke data structures. Metafield and Metaobject definitions provide a schema and configuration for values to follow.",
    category: APICategory.CONFIGURATION,
    visibility: Visibility.PUBLIC,
    searchable: false
  },
  "app-store-review": {
    displayName: "App Store Review",
    description: "Run a pre-submission compliance check against your Shopify app's codebase. Reviews App Store requirements and surfaces likely issues before you submit for official review.",
    category: APICategory.GUIDANCE,
    visibility: Visibility.PUBLIC,
    searchable: false,
    compatibility: "Claude Code, Claude Desktop, Cursor"
  },
  "onboarding-dev": {
    displayName: "Developer Onboarding",
    description: "Get started building on Shopify. Use when a developer asks to build an app, build a theme, create a dev store, set up a partner account, scaffold a project, or get started developing for Shopify. NOT for merchants managing stores.",
    category: APICategory.GUIDANCE,
    visibility: Visibility.PUBLIC,
    searchable: false,
    compatibility: "Claude Code, Claude Desktop, Cursor"
  },
  "onboarding-merchant": {
    displayName: "Merchant Onboarding",
    description: "Set up and connect a Shopify store from your AI assistant. Use when the user wants to: set up my Shopify store, connect my store, install Shopify plugin, get started with Shopify, manage my store, add products to my store, merchant onboarding, start selling online, Shopify setup help, create my first store, how do I set up an online store, import products, migrate from Square, migrate from WooCommerce, migrate from Etsy, migrate from Amazon, migrate from eBay, migrate from Wix, import from Google Merchant Center, migrate from Clover, migrate from Lightspeed, move products to Shopify, import catalog, replatform to Shopify. This is for store owners \u2014 not developers.",
    category: APICategory.GUIDANCE,
    visibility: Visibility.PUBLIC,
    searchable: false,
    compatibility: "Claude Code, Claude Desktop, Cursor",
    frontmatterExtras: { context: "fork", maintainer: "Shopify" }
  }
});

// src/validation/formatCode.ts
function generateMissingImports(packageNames, extensionTarget) {
  return packageNames.map((packageName) => {
    if (extensionTarget && packageName.includes("@shopify/ui-extensions")) {
      return `import '${packageName}/${extensionTarget}';`;
    }
    return `import '${packageName}';`;
  }).join("\n");
}
function addShopifyImports(code2, packageNames, extensionTarget) {
  if (packageNames.includes("@shopify/ui-extensions") && !extensionTarget) {
    throw new Error("Invalid input: extensionTarget is required");
  }
  const generatedImports = generateMissingImports(
    packageNames,
    extensionTarget
  );
  if (code2 && (code2.includes("const shopify =") || code2.includes("globalThis.shopify"))) {
    return generatedImports;
  }
  const shopifyGlobalDeclaration = packageNames.find((pkg) => pkg.includes("@shopify/ui-extensions")) && extensionTarget ? `interface ShopifyApiOverride extends Omit<import('@shopify/ui-extensions/${extensionTarget}').Api, 'query'> { query: (...args: any[]) => Promise<{ data: any; errors?: any[] }>; } const shopify: ShopifyApiOverride = (globalThis as any).shopify;` : "";
  const shopifyImports = `${generatedImports}
${shopifyGlobalDeclaration}`.trim();
  return shopifyImports;
}
function formatCode(code2, packageNames, extensionTarget) {
  if (code2.includes("!DOCTYPE") || code2.includes("!html")) {
    const bodyContent = code2.match(/<body>(.*?)<\/body>/s)?.[1];
    if (bodyContent) {
      code2 = `<>${bodyContent}</>`;
    }
  }
  const shopifyImports = addShopifyImports(code2, packageNames, extensionTarget);
  const codeWithImports = `
${shopifyImports}
${code2}
`;
  return codeWithImports;
}

// src/validation/createVirtualTSEnvironment.ts
import * as path from "path";
import ts from "typescript";
import { fileURLToPath } from "url";
var getCompilerOptions = (jsxImportSource) => ({
  target: ts.ScriptTarget.ESNext,
  module: ts.ModuleKind.ESNext,
  jsx: ts.JsxEmit.ReactJSX,
  jsxImportSource: jsxImportSource || "preact",
  strict: true,
  strictNullChecks: false,
  esModuleInterop: true,
  skipLibCheck: true,
  moduleResolution: ts.ModuleResolutionKind.NodeJs,
  allowSyntheticDefaultImports: true,
  lib: ["es2020", "dom"],
  allowJs: true,
  checkJs: false
});
function getPackageRoot() {
  const currentDir = fileURLToPath(import.meta.url);
  return path.resolve(currentDir, "../..");
}
function getScriptSnapshot(fileName, virtualFiles) {
  const virtualContent = virtualFiles.get(fileName);
  if (virtualContent) {
    return ts.ScriptSnapshot.fromString(virtualContent);
  }
  try {
    const fileContent = ts.sys.readFile(fileName);
    return fileContent ? ts.ScriptSnapshot.fromString(fileContent) : void 0;
  } catch {
    return void 0;
  }
}
function createLanguageServiceHost(vfs, packageRoot, jsxImportSource) {
  return {
    getScriptFileNames: () => Array.from(vfs.virtualFiles.keys()),
    getScriptVersion: (fileName) => vfs.fileVersions.get(fileName)?.toString() || "0",
    getScriptSnapshot: (fileName) => getScriptSnapshot(fileName, vfs.virtualFiles),
    getCurrentDirectory: () => packageRoot,
    getCompilationSettings: () => getCompilerOptions(jsxImportSource),
    getDefaultLibFileName: (options) => ts.getDefaultLibFilePath(options),
    fileExists: (fileName) => vfs.virtualFiles.has(fileName) || ts.sys.fileExists(fileName),
    readFile: (fileName) => vfs.virtualFiles.get(fileName) || ts.sys.readFile(fileName),
    readDirectory: ts.sys.readDirectory,
    getDirectories: ts.sys.getDirectories,
    directoryExists: ts.sys.directoryExists,
    getNewLine: () => "\n"
  };
}
function createVirtualTSEnvironment(apiName2) {
  const fileVersions = /* @__PURE__ */ new Map();
  const virtualFiles = /* @__PURE__ */ new Map();
  const packageRoot = getPackageRoot();
  const jsxImportSource = apiName2 === "hydrogen" ? "react" : "preact";
  const servicesHost = createLanguageServiceHost(
    { fileVersions, virtualFiles },
    packageRoot,
    jsxImportSource
  );
  const languageService = ts.createLanguageService(
    servicesHost,
    ts.createDocumentRegistry()
  );
  const libDir = path.dirname(
    ts.getDefaultLibFilePath(getCompilerOptions(jsxImportSource))
  );
  const libFileNames = [
    "lib.es5.d.ts",
    // Essential: Contains Partial, Pick, Required, Omit, etc.
    "lib.es2020.d.ts",
    // ES2020 features
    "lib.dom.d.ts"
    // DOM types
  ];
  for (const libFileName of libFileNames) {
    try {
      const libPath = path.join(libDir, libFileName);
      const libContent = ts.sys.readFile(libPath);
      if (libContent) {
        virtualFiles.set(libPath, libContent);
        fileVersions.set(libPath, 1);
      }
    } catch {
    }
  }
  return {
    languageService,
    servicesHost,
    fileVersions,
    virtualFiles
  };
}
function incrementFileVersion(fileVersions, fileName) {
  const currentVersion = fileVersions.get(fileName) || 0;
  const newVersion = currentVersion + 1;
  fileVersions.set(fileName, newVersion);
  return newVersion;
}
function addFileToVirtualEnv(virtualEnv, fileName, content) {
  virtualEnv.virtualFiles.set(fileName, content);
  incrementFileVersion(virtualEnv.fileVersions, fileName);
}

// ../../node_modules/.pnpm/html-tags@5.1.0/node_modules/html-tags/html-tags.json
var html_tags_default = [
  "a",
  "abbr",
  "address",
  "area",
  "article",
  "aside",
  "audio",
  "b",
  "base",
  "bdi",
  "bdo",
  "blockquote",
  "body",
  "br",
  "button",
  "canvas",
  "caption",
  "cite",
  "code",
  "col",
  "colgroup",
  "data",
  "datalist",
  "dd",
  "del",
  "details",
  "dfn",
  "dialog",
  "div",
  "dl",
  "dt

... [Content truncated, total 69,674 chars] ...