export * from 'https://cdn.deno.land/cqhttp_bot/versions/v0.1.5/raw/deno_dist/mod.ts'
export * from "https://deno.land/x/mongo@v0.23.1/mod.ts"

// 加载环境变量
export const es_uri = Deno.env.get("es")!
export const mongo = Deno.env.get("mongo")!
export const ws_url = Deno.env.get("ws_url")!