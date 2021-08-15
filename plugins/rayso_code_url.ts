import { CqMessageEvent, QuickReply, base64  } from '../deps.ts'
import { find_first } from './utils.ts'

/** 返回ray.so的网址 */
export default async function rayso_code_url(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    let lang = find_first(msg.message, /(?<=```)[a-z]+/gm) || "auto"
    lang = language_alias(lang)

    let message = msg.message as string
    let code = message.replace(/^```.*\r*\n/gm, "") //删除首行
    code = code.replace(/\n```.*/gm, "") //删除尾行

    let url = getimgurl(code, lang)

    return msg.quick_reply(`code: ${url}`)
}

function getimgurl(code: string, lang: string = "auto"): string {

    code = code.replace('\r\n','\n') //替换换行，不然会中文乱码
    let CODE = base64.encode(code)
    let TITLE = "Untitled"

    // Customization:
    // Set colors. Available options: candy, breeze, midnight or sunset
    let COLORS = "breeze"
    // Toggle background. Available options: true or false
    let BACKGROUND = "true"
    // Toggle dark mode. Available options: true or false
    let DARK_MODE = "true"
    // Set padding. Available options: 16, 32, 64 or 128
    let PADDING = "32"
    // Set language. Available options: shell, c-like (C++), csharp, clojure, coffeescript, crystal, css, d, dart, diff, dockerfile, elm, erlang, fortran, gherkin,
    // go, groovy, haskell, xml, java, javascript, json, jsx, julia, kotlin, latex, lisp, lua, markdown, mathematica, octave, nginx, objectivec, ocaml (F#), perl, php,
    // powershell, python, r, ruby, rust, scala, smalltalk, sql, swift, typescript, (for Tsx, use jsx), twig, verilog, vhdl, xquery, yaml
    let LANGUAGE = language_alias(lang)


    let url = `https://rayso-proxy.coolrc.workers.dev/?
        colors=${COLORS}
        &background=${BACKGROUND}
        &darkMode=${DARK_MODE}
        &padding=${PADDING}
        &title=${TITLE}
        &code=${CODE}
        &language=${LANGUAGE}`

    //替换所有的换行符
    url = url.replace(/\r\n/g,"")
    url = url.replace(/\n/g,"");
    
    //替换所有的空格（中文空格、英文空格都会被替换）
    url = url.replace(/\s/g,"");
    

    return url
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