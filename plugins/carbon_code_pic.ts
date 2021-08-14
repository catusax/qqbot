import { CqMessageEvent, QuickReply } from '../deps.ts'
import { find_first } from './utils.ts'

/** 渲染代码的高亮图片 */
export default async function carbon_code_pic(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    let lang = find_first(msg.message, /(?<=```)[a-z]+/gm) || "auto"
    lang = language_alias(lang)

    let message = msg.message as string
    let code = message.replace(/^```.*\r*\n/gm, "") //删除首行
    code = code.replace(/\n```.*/gm, "") //删除尾行

    let url = await getimgbase64(code, lang)
    let base64 = url.replace(/data:image\/png;base64,/, "base64://") //不支持DataURL，需要转换成base64://的格式

    return msg.quick_reply('[CQ:image,file=' + base64 + ']')
}

async function getimgbase64(code: string, lang: string = "auto"): Promise<string> {

    let res = await fetch("https://carbonara.vercel.app/api/cook", {
        method: "POST",
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(
            {
                "code": code,
                "language": lang,
                "theme": "shades-of-purple",
                // "exportSize": "1x",
                "backgroundColor":"rgba(255,255,255,0)"
            }
        )
    })

    if (res.status != 200) {
        throw "failed to connect to carbonara.vercel.app，code:" + res.statusText
    }

    return await convertBlobToBase64(await res.blob()) as string
}

const convertBlobToBase64 = (blob: Blob) => new Promise((resolve, reject) => {
    const reader = new FileReader;
    reader.onerror = reject;
    reader.onload = () => {
        resolve(reader.result);
    };
    reader.readAsDataURL(blob);
});

function language_alias(lang:string){
    let lang_map = new Map()
    lang_map.set("js","javascript")
    lang_map.set("py","python")
    lang_map.set("c++","cpp")
    lang_map.set("ts","typescript")

    if (lang_map.has(lang)) lang = lang_map.get(lang)
    return lang
}


import { assertEquals } from "https://deno.land/std@0.104.0/testing/asserts.ts";
Deno.test("carbon_code_pic",
    async () => {
        let code = `Deno.test({
            name: "testing example",
            fn(): void {
              assertEquals("world", "world");
              assertEquals({ hello: "world" }, { hello: "world" });
            },
          });`
        let img = await getimgbase64(code, "js")
        // console.log(img)
        assertEquals(true, img.length >= 1000); //url比较长就应该是图片
    },
);

Deno.test("get code from markdown",
    async () => {
        let code = "```js\nlet a=1\n```"
        code = code.replaceAll(/```.*\n/gm, "") //删除首行
        console.log("code: " + code)
        code = code.replaceAll(/\n```.*/gm, "") //删除尾行
        console.log("code2: " + code)
        assertEquals(code,"let a=1")
    }
)