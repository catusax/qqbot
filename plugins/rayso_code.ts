import { CqMessageEvent, QuickReply, base64, rayso_api  } from '../deps.ts'
import { find_first } from './utils.ts'

/** 返回ray.so的网址 */
export default async function rayso_code_pic(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    let lang = find_first(msg.message, /(?<=```)[a-z]+/gm) || "auto"
    lang = language_alias(lang)

    let message = msg.message as string
    let code = message.replace(/^```.*\r*\n/gm, "") //删除首行
    code = code.replace(/\n```.*/gm, "") //删除尾行

    let img = await getimgbase64(code) // 暂时不支持换语言
    // console.log()

    return msg.quick_reply('[CQ:image,file=base64://' + img + ']')
}

async function getimgbase64(code: string, lang: string = "auto"): Promise<string> {

    code = code.replace('\r\n','\n') //替换换行，不然会中文乱码
    let CODE = base64.encode(code)
    let PADDING = 32

    let url = `${rayso_api}?`+
    `content=${CODE}`+
    `&font=Fira%20code` +
    `&padding=${PADDING}` +
    `&size=1`

    let res = await (await fetch(url)).json() as {ok:number,msg:string,data:string|null}
    if (res.ok == 200)
    return res.data!
    else throw "获取图片失败："+res.msg
}


function language_alias(lang: string) {
    let langs = [
        "shell","cpp","csharp","clojure","coffeescript","crystal","css",
        "d","dart","diff","dockerfile","elm","erlang","fortran","fsharp","gherkin","go","groovy",
        "haskell","java","javascript","json","jsx","julia",
        "kotlin","latex","lisp","lua","markdown","mathematica","octave","nginx","objectivec","ocaml",
        "perl","php","powershell","python","r","ruby","rust","scala","smalltalk", "sql","swift","typescript",
        "tsx","twig","verilog","vhdl","xquery","xml","yaml",
    ]

    if (langs.includes(lang)) return lang

    let lang_map = new Map()
    lang_map.set("js", "javascript")
    lang_map.set("py", "python")
    lang_map.set("c++", "cpp")
    lang_map.set("ts", "typescript")
    lang_map.set("c#","csharp")
    lang_map.set("f#","fsharp")
    lang_map.set("bash","shell")
    lang_map.set("sh","shell")

    if (lang_map.has(lang)) return lang_map.get(lang)

    return "auto"
}

import { assertEquals } from "https://deno.land/std@0.104.0/testing/asserts.ts";

Deno.test("get code from markdown",
    async () => {
        let code = "```js\nlet a=1\n```"
        code = code.replaceAll(/```.*\n/gm, "") //删除首行
        console.log("code: " + code)
        code = code.replaceAll(/\n```.*/gm, "") //删除尾行
        console.log("code2: " + code)
        assertEquals(code, "let a=1")
    }
)