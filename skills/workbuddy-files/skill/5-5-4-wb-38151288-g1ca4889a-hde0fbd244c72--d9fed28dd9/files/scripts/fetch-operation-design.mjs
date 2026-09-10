const CATALOG_URL = 'https://static.d.gtimg.com/templates/operation.json';
const DESIGN_HOSTNAME = 'static.d.gtimg.com';
const REQUEST_TIMEOUT_MS = 15_000;
const MAX_DESIGN_BYTES = 1024 * 1024;

const cacheBust = () => `${Date.now()}${Math.random().toString(36).slice(2, 10)}`;
const isRecord = value => !!value && typeof value === 'object' && !Array.isArray(value);

function validateDesignUrl(rawUrl) {
    const designUrl = new URL(rawUrl);
    if (
        designUrl.protocol !== 'https:'
        || designUrl.hostname !== DESIGN_HOSTNAME
    ) {
        throw new Error('Unsupported operation design URL');
    }
    designUrl.searchParams.set('t', cacheBust());
    return designUrl;
}

async function readTextWithinLimit(response) {
    const contentLength = response.headers.get('content-length');
    if (contentLength !== null && Number(contentLength) > MAX_DESIGN_BYTES) {
        throw new Error('Operation style Markdown exceeds size limit');
    }
    if (!response.body) {
        throw new Error('Operation style Markdown response has no body');
    }

    const reader = response.body.getReader();
    const chunks = [];
    let totalBytes = 0;
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }
            totalBytes += value.byteLength;
            if (totalBytes > MAX_DESIGN_BYTES) {
                await reader.cancel('Operation style Markdown exceeds size limit');
                throw new Error('Operation style Markdown exceeds size limit');
            }
            chunks.push(value);
        }
    } finally {
        reader.releaseLock();
    }

    const body = new Uint8Array(totalBytes);
    let offset = 0;
    for (const chunk of chunks) {
        body.set(chunk, offset);
        offset += chunk.byteLength;
    }
    return new TextDecoder().decode(body);
}

async function main() {
    const styleId = process.argv[2]?.trim();
    if (!styleId) {
        throw new Error('Usage: node scripts/fetch-operation-design.mjs <styleId>');
    }

    const catalogResponse = await fetch(`${CATALOG_URL}?t=${cacheBust()}`, {
        redirect: 'error',
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!catalogResponse.ok) {
        throw new Error(`Failed to fetch operation catalog: HTTP ${catalogResponse.status}`);
    }

    const catalog = await catalogResponse.json();
    if (!Array.isArray(catalog)) {
        throw new Error('Unexpected operation catalog shape: expected an array');
    }
    const item = catalog
        .filter(group => isRecord(group) && group.is_display !== false)
        .flatMap(group => Array.isArray(group.children) ? group.children : [])
        .find(child => (
            isRecord(child)
            && child.id === styleId
            && typeof child.design === 'string'
            && child.design.trim()
        ));
    if (!item) {
        throw new Error(`Operation style not found or missing design URL: ${styleId}`);
    }

    const designUrl = validateDesignUrl(item.design.trim());
    const designResponse = await fetch(designUrl, {
        redirect: 'error',
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!designResponse.ok) {
        throw new Error(`Failed to fetch operation style Markdown: HTTP ${designResponse.status}`);
    }

    const markdown = await readTextWithinLimit(designResponse);
    if (!markdown.trim()) {
        throw new Error(`Operation style Markdown is empty: ${styleId}`);
    }
    process.stdout.write(markdown.endsWith('\n') ? markdown : `${markdown}\n`);
}

main().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
});
