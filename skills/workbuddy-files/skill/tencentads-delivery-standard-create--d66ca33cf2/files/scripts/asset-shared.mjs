/**
 * asset-shared.mjs — get-assets.mjs 和 get-assets-by-rules.mjs 的共享模块
 *
 * 包含：
 * - 分类常量（ONEID_TYPES, CHANNELS_LIVE_TYPES, CATALOG_TYPES 等）
 * - 载体常量（CARRIER_NOT_NEEDED, CARRIER_PROMOTED_OBJECT_MAP 等）
 * - 资产查询函数（fetchOneidAssets, fetchChannelsLiveAssets, fetchCatalogAssets 等）
 * - 载体查询函数（fetchCarriersPage, matchCarrier）
 * - 通用工具（callAvailableMarketingAssets, buildFlatParams）
 */

import { callApi } from "tencentads-cli";
import { callAvailableMarketingAssets } from "./get-available-marketing-assets.mjs";

export { callAvailableMarketingAssets };

// ═══════════════════════════════════════════════════════════════
// 分类常量
// ═══════════════════════════════════════════════════════════════

// 不需要填写 marketing_carrier_id 的载体类型
export const CARRIER_NOT_NEEDED = new Set([
  "MARKETING_CARRIER_TYPE_JUMP_PAGE",
  "MARKETING_CARRIER_TYPE_JUMP_PAGE2",
  "MARKETING_CARRIER_TYPE_UNKNOWN",
]);

// 通过 bff_promoted_objects/get 查询载体的载体类型 → 对应的 promoted_object_type
export const CARRIER_PROMOTED_OBJECT_MAP = {
  "MARKETING_CARRIER_TYPE_APP_ANDROID": "PROMOTED_OBJECT_TYPE_APP_ANDROID",
  "MARKETING_CARRIER_TYPE_APP_IOS": "PROMOTED_OBJECT_TYPE_APP_IOS",
  "MARKETING_CARRIER_TYPE_APP_HARMONY": "PROMOTED_OBJECT_TYPE_HARMONY_APP",
  "MARKETING_CARRIER_TYPE_APP_QUICK_APP": "PROMOTED_OBJECT_TYPE_APP_QUICK_APP",
  "MARKETING_CARRIER_TYPE_WECHAT_CHANNELS_LIVE": "PROMOTED_OBJECT_TYPE_WECHAT_CHANNELS",
  "MARKETING_CARRIER_TYPE_WECHAT_CHANNELS": "PROMOTED_OBJECT_TYPE_WECHAT_CHANNELS",
  "MARKETING_CARRIER_TYPE_WECHAT_CHANNELS_LIVE_RESERVATION": "PROMOTED_OBJECT_TYPE_WECHAT_CHANNELS",
  "MARKETING_CARRIER_TYPE_WECHAT_OFFICIAL_ACCOUNT": "PROMOTED_OBJECT_TYPE_WECHAT_OFFICIAL_ACCOUNT",
  "MARKETING_CARRIER_TYPE_WECHAT_MINI_GAME": "PROMOTED_OBJECT_TYPE_MINI_GAME_WECHAT",
  "MARKETING_CARRIER_TYPE_MINI_PROGRAM_WECHAT": "PROMOTED_OBJECT_TYPE_MINI_PROGRAM_WECHAT",
  "MARKETING_CARRIER_TYPE_PC_GAME": "PROMOTED_OBJECT_TYPE_APP_PC",
  "MARKETING_CARRIER_TYPE_QQ_MINI_GAME": "PROMOTED_OBJECT_TYPE_MINI_GAME_QQ",
};

// bff_promoted_objects/get 接口的 filtering.values 必须传数字值
export const PROMOTED_OBJECT_TYPE_VALUE_MAP = {
  "PROMOTED_OBJECT_TYPE_APP_ANDROID": "12",
  "PROMOTED_OBJECT_TYPE_APP_IOS": "19",
  "PROMOTED_OBJECT_TYPE_WECHAT_OFFICIAL_ACCOUNT": "23",
  "PROMOTED_OBJECT_TYPE_ECOMMERCE": "30",
  "PROMOTED_OBJECT_TYPE_LINK_WECHAT": "31",
  "PROMOTED_OBJECT_TYPE_APP_ANDROID_MYAPP": "35",
  "PROMOTED_OBJECT_TYPE_APP_ANDROID_UNION": "38",
  "PROMOTED_OBJECT_TYPE_LOCAL_ADS_WECHAT": "39",
  "PROMOTED_OBJECT_TYPE_LEAD_AD": "43",
  "PROMOTED_OBJECT_TYPE_QQ_BROWSER_MINI_PROGRAM": "45",
  "PROMOTED_OBJECT_TYPE_MINI_GAME_WECHAT": "46",
  "PROMOTED_OBJECT_TYPE_APP_ANDROID_GOOGLE_PLAY": "48",
  "PROMOTED_OBJECT_TYPE_MINI_GAME_QQ": "49",
  "PROMOTED_OBJECT_TYPE_WECHAT_CHANNELS": "51",
  "PROMOTED_OBJECT_TYPE_MINI_PROGRAM_WECHAT": "52",
  "PROMOTED_OBJECT_TYPE_APP_QUICK_APP": "53",
  "PROMOTED_OBJECT_TYPE_HARMONY_APP": "55",
  "PROMOTED_OBJECT_TYPE_APP_PC": "4",
};

export function resolvePromotedObjectTypeValue(promotedObjectType) {
  return PROMOTED_OBJECT_TYPE_VALUE_MAP[promotedObjectType] || promotedObjectType;
}

// ONEID 类：返回 marketing_asset_outer_id
// 统一含门店、门店包、企业微信、微信小游戏（查询路径在 fetchOneidAssets 内部路由）
export const ONEID_TYPES = new Set([
  "MARKETING_TARGET_TYPE_APP_ANDROID",
  "MARKETING_TARGET_TYPE_APP_IOS",
  "MARKETING_TARGET_TYPE_APP_HARMONY",
  "MARKETING_TARGET_TYPE_MINI_PROGRAM_WECHAT",
  "MARKETING_TARGET_TYPE_WECHAT_OFFICIAL_ACCOUNT",
  "MARKETING_TARGET_TYPE_MINI_GAME_QQ",
  "MARKETING_TARGET_TYPE_PC_GAME",
  "MARKETING_TARGET_TYPE_APP_QUICK_APP",
  "MARKETING_TARGET_TYPE_LOCAL_STORE",
  "MARKETING_TARGET_TYPE_LOCAL_STORE_PACKAGE",
  "MARKETING_TARGET_TYPE_WECHAT_WORK",
  "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME",
]);

// ONEID 类中支持 bff_promoted_objects/get 的 target_type → promoted_object_type 数字值
// BFF 返回已绑定的应用（范围更大），AMA 只返回已创建过资产的（子集）
export const ONEID_BFF_MAP = {
  "MARKETING_TARGET_TYPE_APP_ANDROID": "12",
  "MARKETING_TARGET_TYPE_APP_IOS": "19",
  "MARKETING_TARGET_TYPE_APP_HARMONY": "55",
  "MARKETING_TARGET_TYPE_APP_QUICK_APP": "53",
  "MARKETING_TARGET_TYPE_MINI_PROGRAM_WECHAT": "52",
  "MARKETING_TARGET_TYPE_WECHAT_OFFICIAL_ACCOUNT": "23",
  "MARKETING_TARGET_TYPE_MINI_GAME_QQ": "49",
  "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME": "46",
  // PC_GAME 不支持 BFF（报错 1000000），只走 AMA
};

// 视频号直播类：通过 promoted_objects/get (mktapi/proxy) 接口查询
export const CHANNELS_LIVE_TYPES = new Set([
  "MARKETING_TARGET_TYPE_WECHAT_CHANNELS",
  "MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE",
  "MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE_RESERVATION",
]);

export const CATALOG_TYPES = new Set([
  "MARKETING_TARGET_TYPE_CONSUMER_PRODUCT",
  "MARKETING_TARGET_TYPE_COMMODITY_SET",
  "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT",
  "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT_SET",
  "MARKETING_TARGET_TYPE_WECHAT_STORE",
]);

// 商品库类回退映射：CONSUMER_PRODUCT ↔ WECHAT_STORE_PRODUCT 互为回退
export const CATALOG_FALLBACK_MAP = {
  "MARKETING_TARGET_TYPE_CONSUMER_PRODUCT": "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT",
  "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT": "MARKETING_TARGET_TYPE_CONSUMER_PRODUCT",
};

// 所有 ONEID-like 类型的合集（用于 asset_id 短路判断 + 创建时走 marketing_asset_outer_spec）
// = ONEID_TYPES + CHANNELS_LIVE_TYPES
export const ALL_ONEID_LIKE_TYPES = new Set([
  ...ONEID_TYPES,
  ...CHANNELS_LIVE_TYPES,
]);

// 创建时需要使用 marketing_asset_outer_spec 的 target_type 白名单
// = ALL_ONEID_LIKE_TYPES ∪ CATALOG_TYPES（行业产品库走 marketing_asset_id，不在此集合中）
// 供 create-adgroup.mjs 使用
export const SPEC_REQUIRED_TARGET_TYPES = new Set([
  ...ALL_ONEID_LIKE_TYPES,
  ...CATALOG_TYPES,
]);

// 行业产品库类：创建时走 marketing_asset_id（非 spec），需显式列出已知类型。
// 不在任何分类集合中的未知 target_type 将被放行交由 API 判断，避免新增类型被误拦截。
export const INDUSTRY_TYPES = new Set([
  "MARKETING_TARGET_TYPE_PRODUCT",
  "MARKETING_TARGET_TYPE_TRAFFIC",
  "MARKETING_TARGET_TYPE_CONSUME_MEDICAL",
  "MARKETING_TARGET_TYPE_COMPREHENSIVE_HOUSEKEEPING",
  "MARKETING_TARGET_TYPE_FICTION",
  "MARKETING_TARGET_TYPE_SHORT_DRAMA",
  "MARKETING_TARGET_TYPE_AUDIOVISUAL_ENTERTAINMENT",
  "MARKETING_TARGET_TYPE_BEAUTY_AND_PERSONAL_CARE",
  "MARKETING_TARGET_TYPE_WEDDING_AND_PORTRAIT_PHOTOGRAPHY",
  "MARKETING_TARGET_TYPE_FRANCHISE_BRAND",
  "MARKETING_TARGET_TYPE_ENTERPRISE_SERVICES",
  "MARKETING_TARGET_TYPE_EXHIBITION_BOOTH_DESIGN",
  "MARKETING_TARGET_TYPE_INSURANCE",
  "MARKETING_TARGET_TYPE_BANK",
  "MARKETING_TARGET_TYPE_CREDIT",
  "MARKETING_TARGET_TYPE_INVESTMENT_CONSULTING",
  "MARKETING_TARGET_TYPE_REAL_ESTATE",
  "MARKETING_TARGET_TYPE_TELECOMMUNICATIONS_OPERATOR",
  "MARKETING_TARGET_TYPE_TOURIST_ATTRACTIONS_TICKETS",
  "MARKETING_TARGET_TYPE_RENOVATION_SERVICES",
  "MARKETING_TARGET_TYPE_FURNITURE_AND_BUILDING_MATERIALS",
  "MARKETING_TARGET_TYPE_EXHIBITION_SALES",
  "MARKETING_TARGET_TYPE_MEDICINE_INDUSTRY_COMMERCIAL",
  "MARKETING_TARGET_TYPE_FINANCE",
  "MARKETING_TARGET_TYPE_CATERING_AND_LEISURE",
  "MARKETING_TARGET_TYPE_CHAIN_RESTAURANT",
  "MARKETING_TARGET_TYPE_TOURIST_TRAVEL_ROUTE",
  "MARKETING_TARGET_TYPE_TOURIST_CRUISE_LINE",
  "MARKETING_TARGET_TYPE_TOURIST_HOTEL_SERVICE",
  "MARKETING_TARGET_TYPE_TOURIST_AIRLINE_TICKETS",
  "MARKETING_TARGET_TYPE_LOCAL_STORE_COMBINE_WITH_PRODUCT",
  "MARKETING_TARGET_TYPE_ACTIVITY",
  "MARKETING_TARGET_TYPE_STORE",
  "MARKETING_TARGET_TYPE_LIVE_STREAM_ROOM",
  "MARKETING_TARGET_TYPE_PERSONAL_STORE",
  "MARKETING_TARGET_TYPE_PLATFORM_CHANNEL",
  "MARKETING_TARGET_TYPE_TWO_WHEEL_VEHICLE",
  "MARKETING_TARGET_TYPE_GOVERNMENT_AFFAIRS",
  "MARKETING_TARGET_TYPE_CAR_ECOLOGY",
  "MARKETING_TARGET_TYPE_PRODUCT_AGGREGATION_PAGE",
  "MARKETING_TARGET_TYPE_RESALE_AND_COMMERCIAL_LAND",
  "MARKETING_TARGET_TYPE_VIDEO_PROGRAM",
  "MARKETING_TARGET_TYPE_FUN_TEST",
  "MARKETING_TARGET_TYPE_MATERNITY_PARENTING",
  "MARKETING_TARGET_TYPE_LEISURE_ENTERTAINMENT",
]);

// ═══════════════════════════════════════════════════════════════
// BFF promoted_objects 通用查询（支持分页）
// ═══════════════════════════════════════════════════════════════

/**
 * 通过 bff_promoted_objects/get 查询指定 promoted_object_type 的列表（支持自动翻页）
 * @returns {{ list: Array, totalNumber: number }}
 */
export async function fetchBffPromotedObjects(accountId, promotedObjectTypeValue, { maxPages = 100 } = {}) {
  const result = await callApi({
    method: "GET",
    path: "/v3.0/bff_promoted_objects/get",
    accountId: String(accountId),
    params: {
      account_id: parseInt(accountId, 10),
      filtering: [
        { field: "promoted_object_type", operator: "EQUALS", values: [promotedObjectTypeValue] },
      ],
      page: 1,
      page_size: 100,
      fields: ["promoted_object_type", "promoted_object_id", "promoted_object_name", "promoted_object_spec"],
    },
  });

  if (!result.success) return { list: [], totalNumber: 0 };

  const data = result.data?.data ?? result.data ?? {};
  let list = data.list ?? [];
  const pageInfo = data.page_info ?? {};
  const totalNumber = pageInfo.total_number ?? list.length;

  // 自动翻页
  if (totalNumber > list.length) {
    const totalPages = Math.min(Math.ceil(totalNumber / 100), maxPages);
    for (let page = 2; page <= totalPages; page++) {
      const nextResult = await callApi({
        method: "GET",
        path: "/v3.0/bff_promoted_objects/get",
        accountId: String(accountId),
        params: {
          account_id: parseInt(accountId, 10),
          filtering: [
            { field: "promoted_object_type", operator: "EQUALS", values: [promotedObjectTypeValue] },
          ],
          page,
          page_size: 100,
          fields: ["promoted_object_type", "promoted_object_id", "promoted_object_name", "promoted_object_spec"],
        },
      });
      if (!nextResult.success) break;
      const nextList = nextResult.data?.data?.list ?? nextResult.data?.list ?? [];
      if (nextList.length === 0) break;
      list = list.concat(nextList);
    }
  }

  return { list, totalNumber };
}

/**
 * 将 bff_promoted_objects/get 返回的 list 转为标准 ONEID 资产格式
 */
export function mapBffListToOneidAssets(list, targetType) {
  return list.map((item) => ({
    marketing_asset_outer_id: item.promoted_object_id ?? "",
    marketing_carrier_id: item.promoted_object_id ?? "",
    name: item.promoted_object_name ?? "",
    type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
  }));
}

// ═══════════════════════════════════════════════════════════════
// 资产查询函数（按 target_type 分类路由）
// ═══════════════════════════════════════════════════════════════

/**
 * 统一路由入口：根据 targetType 调用对应的查询函数
 * @param {object} [opts] - { hint: { asset_id, asset_name }, includeLiveNotices: boolean }
 *   hint: 用于提前退出翻页（by-rules 传 match_hint，get-assets 传 asset_hint）
 *   includeLiveNotices: 是否查询直播预约场次（仅 get-assets.mjs 需要）
 */
export async function fetchAssetsForTargetType(accountId, targetType, opts = {}) {
  if (CHANNELS_LIVE_TYPES.has(targetType)) {
    return await fetchChannelsLiveAssets(accountId, targetType, opts);
  } else if (ONEID_TYPES.has(targetType)) {
    return await fetchOneidAssets(accountId, targetType, opts);
  } else if (CATALOG_TYPES.has(targetType)) {
    return await fetchCatalogAssets(accountId, targetType, opts);
  } else {
    return await fetchIndustryAssets(accountId, targetType, opts);
  }
}

// ─── 视频号直播类 ───

async function fetchChannelsLiveAssets(accountId, targetType, opts = {}) {
  const promotedObjectType = "PROMOTED_OBJECT_TYPE_WECHAT_CHANNELS";
  const potValue = resolvePromotedObjectTypeValue(promotedObjectType);

  const { list } = await fetchBffPromotedObjects(accountId, potValue);

  if (list.length === 0) {
    return { asset_type: "ONEID", assets: [] };
  }

  const assets = mapBffListToOneidAssets(list, targetType);

  // 直播预约类：额外获取每个视频号下的直播预约场次
  const isLiveReservation = targetType === "MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE_RESERVATION";
  let liveNotices = null;

  if (isLiveReservation && opts.includeLiveNotices && list.length > 0) {
    liveNotices = {};
    for (const item of list) {
      const channelsId = item.promoted_object_id ?? "";
      if (!channelsId) continue;

      const isExport = channelsId.startsWith("export");
      const noticeParams = {
        account_id: parseInt(accountId, 10),
        ...(isExport
          ? { wechat_channels_account_id: channelsId }
          : { finder_username: channelsId }),
      };
      const noticeResult = await callApi({
        method: "GET",
        path: "/v3.0/channels_livenoticeinfo/get",
        accountId: String(accountId),
        params: noticeParams,
      });

      if (!noticeResult.success) continue;

      const noticeData = noticeResult.data?.data ?? noticeResult.data ?? {};
      const noticeList = noticeData.live_notice_record_list ?? [];

      if (noticeList.length > 0) {
        liveNotices[channelsId] = noticeList.map((notice) => ({
          notice_id: notice.notice_id ?? "",
          introduction: notice.introduction ?? "",
          start_time: notice.start_time ?? 0,
          status_wording: notice.status_wording ?? "",
          nickname: notice.nickname ?? "",
        }));
      }
    }
  }

  const output = { asset_type: "ONEID", assets };
  if (liveNotices && Object.keys(liveNotices).length > 0) {
    output.live_notices = liveNotices;
  }
  return output;
}

// ─── ONEID 类（含门店、门店包、企业微信、微信小游戏，统一路由） ───

async function fetchOneidAssets(accountId, targetType, opts = {}) {
  // 门店：通过 local_stores/get 查询
  if (targetType === "MARKETING_TARGET_TYPE_LOCAL_STORE") {
    return await fetchLocalStoreAssets(accountId, targetType, opts);
  }

  // 门店包：通过 local_store_packages/get 查询
  if (targetType === "MARKETING_TARGET_TYPE_LOCAL_STORE_PACKAGE") {
    return await fetchLocalStorePackageAssets(accountId, targetType, opts);
  }

  // 企业微信：通过 csgroup_auth_info 接口
  if (targetType === "MARKETING_TARGET_TYPE_WECHAT_WORK") {
    return await fetchWechatWorkAssets(accountId, opts);
  }

  // 标准 ONEID：优先走 BFF，回退 AMA
  const bffPot = ONEID_BFF_MAP[targetType];
  if (bffPot) {
    try {
      const { list } = await fetchBffPromotedObjects(accountId, bffPot);
      if (list.length > 0) {
        const assets = mapBffListToOneidAssets(list, targetType);
        return { asset_type: "ONEID", assets, source: "bff" };
      }
    } catch {
      // BFF 失败，回退到 AMA
    }
  }

  // 回退：available_marketing_assets/get
  const { list, error } = await callAvailableMarketingAssets(accountId, targetType, { hint: opts.hint });

  if (error && list.length === 0) {
    return { asset_type: "ONEID", assets: [], error: error.message || "API 调用失败" };
  }

  const assets = list.map((item) => {
    // outer_id 提取优先级：直接字段 > spec > info_outer_id > PROMOTED_ASSET_ATTR_KEY_* 属性
    let outerId = item.marketing_asset_outer_id
      || item.marketing_asset_outer_spec?.marketing_asset_outer_id
      || item.info_outer_id
      || "";

    // 回退：从 PROMOTED_ASSET_ATTR_KEY_* 中提取
    if (!outerId) {
      const attrKeys = item.MARKETING_ASSET_ATTR_CLASS_MARKETING;
      if (Array.isArray(attrKeys)) {
        for (const attrKey of attrKeys) {
          const val = item[attrKey];
          if (Array.isArray(val) && val[0]) { outerId = String(val[0]); break; }
        }
      }
    }

    return {
      marketing_asset_outer_id: outerId,
      marketing_carrier_id: outerId,
      name: item.marketing_target_name ?? item.asset_name ?? "",
      type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
    };
  });

  return { asset_type: "ONEID", assets, source: "ama" };
}

// ─── 门店类（通过 /v3.0/local_stores/get） ───

async function fetchLocalStoreAssets(accountId, targetType, opts = {}) {
  const { hint } = opts;
  const hintId = hint?.asset_id != null ? String(hint.asset_id).trim() : null;
  const hintName = hint?.asset_name != null ? String(hint.asset_name).trim() : null;

  const params = {
    account_id: parseInt(accountId, 10),
    page: 1,
    page_size: 100,
  };

  if (hintName) {
    params.filtering = [
      { field: "local_store_name", operator: "CONTAINS", values: [hintName] },
    ];
  }

  let allStores = [];
  let currentPage = 1;

  while (true) {
    params.page = currentPage;
    const result = await callApi({
      method: "GET",
      path: "/v3.0/local_stores/get",
      accountId: String(accountId),
      params,
    });

    if (!result.success) {
      if (allStores.length === 0) return { asset_type: "ONEID", assets: [] };
      break;
    }

    const data = result.data?.data ?? result.data ?? {};
    const list = data.list ?? [];
    if (list.length === 0) break;
    allStores = allStores.concat(list);

    // hint 提前退出
    if (hintId || hintName) {
      const found = list.some((item) => {
        const outerId = `${item.poi_id}@${item.owner_account_id ?? ""}`;
        if (hintId && (String(item.poi_id) === hintId || outerId === hintId)) return true;
        if (hintName) {
          const name = (item.local_store_name ?? "").toLowerCase();
          const lh = hintName.toLowerCase();
          if (name.includes(lh) || lh.includes(name)) return true;
        }
        return false;
      });
      if (found) break;
    }

    const pageInfo = data.page_info ?? {};
    const totalPage = pageInfo.total_page ?? 1;
    if (currentPage >= totalPage) break;
    currentPage++;
  }

  // marketing_asset_outer_id 格式: "poi_id@owner_account_id"
  const assets = allStores
    .filter((item) => item.poi_id)
    .map((item) => ({
      marketing_asset_outer_id: `${item.poi_id}@${item.owner_account_id ?? ""}`,
      marketing_carrier_id: `${item.poi_id}@${item.owner_account_id ?? ""}`,
      name: item.local_store_name ?? "",
      poi_id: item.poi_id,
      owner_account_id: item.owner_account_id,
      province: item.local_store_province ?? "",
      city: item.local_store_city ?? "",
      address: item.local_store_address ?? "",
      type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
    }));

  return { asset_type: "ONEID", assets };
}

// ─── 门店包类（通过 /v3.0/local_store_packages/get） ───

async function fetchLocalStorePackageAssets(accountId, targetType, opts = {}) {
  const { hint } = opts;
  const hintId = hint?.asset_id != null ? String(hint.asset_id).trim() : null;
  const hintName = hint?.asset_name != null ? String(hint.asset_name).trim() : null;

  const params = {
    account_id: parseInt(accountId, 10),
    page: 1,
    page_size: 100,
  };

  if (hintName) {
    params.filtering = [
      { field: "local_store_package_name", operator: "CONTAINS", values: [hintName] },
    ];
  }

  let allPackages = [];
  let currentPage = 1;

  while (true) {
    params.page = currentPage;
    const result = await callApi({
      method: "GET",
      path: "/v3.0/local_store_packages/get",
      accountId: String(accountId),
      params,
    });

    if (!result.success) {
      if (allPackages.length === 0) return { asset_type: "ONEID", assets: [] };
      break;
    }

    const data = result.data?.data ?? result.data ?? {};
    const list = data.list ?? [];
    if (list.length === 0) break;
    allPackages = allPackages.concat(list);

    // hint 提前退出
    if (hintId || hintName) {
      const found = list.some((item) => {
        if (hintId && String(item.local_store_package_id ?? "") === hintId) return true;
        if (hintName) {
          const name = (item.local_store_package_name ?? "").toLowerCase();
          const lh = hintName.toLowerCase();
          if (name.includes(lh) || lh.includes(name)) return true;
        }
        return false;
      });
      if (found) break;
    }

    const pageInfo = data.page_info ?? {};
    const totalPage = pageInfo.total_page ?? 1;
    if (currentPage >= totalPage) break;
    currentPage++;
  }

  // marketing_asset_outer_id = local_store_package_id
  const assets = allPackages
    .filter((item) => item.local_store_package_id != null)
    .map((item) => ({
      marketing_asset_outer_id: String(item.local_store_package_id),
      marketing_carrier_id: String(item.local_store_package_id),
      name: item.local_store_package_name ?? "",
      local_store_package_id: item.local_store_package_id,
      store_count: item.local_store_list?.length ?? 0,
      type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
    }));

  return { asset_type: "ONEID", assets };
}

// ─── 企业微信（通过 csgroup_auth_info 接口） ───

async function fetchWechatWorkAssets(accountId, opts = {}) {
  const result = await callApi({
    method: "GET",
    path: "/v3.0/wechat_pages_csgroup_auth_info/get",
    accountId: String(accountId),
    params: {
      account_id: parseInt(accountId, 10),
    },
  });

  if (!result.success) {
    // 降级：尝试原有的 available_marketing_assets 接口
    const { list } = await callAvailableMarketingAssets(accountId, "MARKETING_TARGET_TYPE_WECHAT_WORK", { hint: opts.hint });
    const assets = list.map((item) => ({
      marketing_asset_outer_id: item.PROMOTED_ASSET_ATTR_KEY_WECHAT_WORK_CORP_ID?.[0] ?? item.marketing_asset_outer_id ?? "",
      marketing_carrier_id: item.PROMOTED_ASSET_ATTR_KEY_WECHAT_WORK_CORP_ID?.[0] ?? item.marketing_asset_outer_id ?? "",
      name: item.marketing_target_name ?? item.asset_name ?? "",
      type: "WECHAT_WORK",
    }));
    return { asset_type: "ONEID", assets };
  }

  const list = result.data?.data?.list ?? result.data?.list ?? [];
  const assets = list.map((item) => ({
    marketing_asset_outer_id: item.corp_id ?? "",
    marketing_carrier_id: item.corp_id ?? "",
    name: item.corp_name || item.corp_id || "",
    type: "WECHAT_WORK",
  }));

  return { asset_type: "ONEID", assets };
}

// ─── 行业产品库类 ───

async function fetchIndustryAssets(accountId, targetType, opts = {}) {
  const { list, error } = await callAvailableMarketingAssets(accountId, targetType, { hint: opts.hint });

  if (error && list.length === 0) {
    return { asset_type: "INDUSTRY", assets: [], error: error.message || "API 调用失败" };
  }

  const assets = list.map((item) => ({
    marketing_asset_id: String(item.marketing_asset_id ?? ""),
    asset_name: item.asset_name ?? "",
    name: item.asset_name || item.marketing_target_name || "",
    description: item.marketing_target_name ?? "",
    type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
  }));

  return { asset_type: "INDUSTRY", assets };
}

// ─── 商品库类（支持 WECHAT_STORE / COMMODITY_SET / 标准商品 + 自动回退） ───

/**
 * @param {object} [opts] - { hint: { asset_id, asset_name }, enableFallback: boolean }
 *   enableFallback: 是否启用 CONSUMER_PRODUCT ↔ WECHAT_STORE_PRODUCT 自动回退（get-assets.mjs 需要）
 */
async function fetchCatalogAssets(accountId, targetType, opts = {}) {
  const result = await queryCatalogAssets(accountId, targetType, opts);

  if (result.assets.length > 0) {
    return { ...result, actual_marketing_target_type: targetType };
  }

  // 回退逻辑（仅 enableFallback=true 时启用）
  if (opts.enableFallback) {
    const fallbackType = CATALOG_FALLBACK_MAP[targetType];
    if (fallbackType) {
      const fallbackResult = await queryCatalogAssets(accountId, fallbackType, opts);
      if (fallbackResult.assets.length > 0) {
        return {
          ...fallbackResult,
          actual_marketing_target_type: fallbackType,
          fallback_applied: true,
          original_marketing_target_type: targetType,
          message: `原始类型 ${targetType} 未找到资产，已自动切换为 ${fallbackType}`,
        };
      }
    }
  }

  return { asset_type: "CATALOG", assets: [], actual_marketing_target_type: targetType };
}

async function queryCatalogAssets(accountId, targetType, opts = {}) {
  const { hint } = opts;
  const hintId = hint?.asset_id != null ? String(hint.asset_id).trim() : null;
  const hintName = hint?.asset_name != null ? String(hint.asset_name).trim() : null;
  const hasHint = !!(hintId || hintName);

  // 推断 catalog_type
  const catalogType = (
    targetType === "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT"
    || targetType === "MARKETING_TARGET_TYPE_WECHAT_STORE"
    || targetType === "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT_SET"
  ) ? "CATALOG_TYPE_CHANNELS_STORE" : "CATALOG_TYPE_STANDARD";

  // 步骤 A: 获取商品目录列表
  const catalogResult = await callApi({
    method: "GET",
    path: "/v3.0/asset_catalog/get",
    accountId: String(accountId),
    params: {
      account_id: parseInt(accountId, 10),
      page: 1,
      page_size: 50,
      catalog_type: catalogType,
    },
  });

  if (!catalogResult.success) {
    return { asset_type: "CATALOG", assets: [] };
  }

  const availableCatalogs = catalogResult.data?.data?.list ?? catalogResult.data?.list ?? [];

  if (availableCatalogs.length === 0) {
    return { asset_type: "CATALOG", assets: [] };
  }

  // ── WECHAT_STORE：不需要查商品列表 ──
  if (targetType === "MARKETING_TARGET_TYPE_WECHAT_STORE") {
    let assets = availableCatalogs
      .filter((catalog) => catalog.wechat_store_id)
      .map((catalog) => ({
        catalog_id: String(catalog.catalog_id ?? ""),
        catalog_name: catalog.catalog_name ?? "",
        wechat_store_id: catalog.wechat_store_id ?? "",
        store_name: catalog.store_name ?? "",
        name: catalog.catalog_name || catalog.store_name || "",
        type: targetType.replace("MARKETING_TARGET_TYPE_", "")

... [Content truncated, total 37,552 chars] ...