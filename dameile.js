/*
    name: "达美乐披萨"
    cron: 27 0,8 * * *
    更新时间:2025-03-01
    登录后玩一把游戏抽奖的时候抓包 https://game.dominos.com.cn/abalone/game/gameDone接口的body,填写到dlm_data,多账号用 @ 分割
*/

// env.js 全局
const $ = new Env("🍕达乐美披萨");
const ckName = "dlm_data";
//-------------------- 一般不动变量区域 -------------------------------------
const Notify = 1;//0为关闭通知,1为打开通知,默认为1
const notify = $.isNode() ? require('./sendNotify') : '';
let envSplitor = ["@"]; //多账号分隔符
let userCookie = ($.isNode() ? process.env[ckName] : $.getdata(ckName)) || '';
let userList = [];
let userIdx = 0;
let userCount = 0;
// 为通知准备的空数组
$.notifyMsg = [];
//bark推送
$.barkKey = ($.isNode() ? process.env["bark_key"] : $.getdata("bark_key")) || '';
//---------------------- 自定义变量区域 -----------------------------------
const giftName = {
    "001": '一等奖 免费披萨券',
    "002": '二等奖 半价披萨券',
    "003": '三等奖 免费嫩汁鸡块券',
    "004": '四等奖 免费任意口味一对烤翅券',
    "005": '五等奖 免费招牌蛋挞',
    "006": '六等奖 免费当季特饮',
}
//脚本入口函数main()
async function main() {
    console.log('\n================== 任务 ==================\n');
    let taskall = [];
    for (let user of userList) {
        if (user.ckStatus) {
            //ck未过期，开始执行任务
            // DoubleLog(`🔷账号${user.index} >> Start work`)
            console.log(`随机延迟${user.getRandomTime()}ms`);
            taskall.push(await user.todoList());
            await $.wait(user.getRandomTime());
        } else {
            //将ck过期消息存入消息数组
            $.notifyMsg.push(`❌账号${user.index} >> Check ck error!`)
        }
    }
    await Promise.all(taskall);
}

class UserInfo {
    constructor(str) {
        this.index = ++userIdx;
        this.ckInfo = str.split("&");
        this.openid = this.ckInfo[0];;
        this.body = str;
        this.ckStatus = true;
        this.drawStatus = true;
        this.sharingStatus = true;
        this.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b13)XWEB/9185",
            'Content-Type': "application/x-www-form-urlencoded",
            'xweb_xhr': "1",
            'Sec-Fetch-Site': "cross-site",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Dest': "empty",
            'Referer': "https://servicewechat.com/wx887bf6ad752ca2f3/62/page-frame.html",
            'Accept-Language': "zh-CN,zh;q=0.9"
        };
    }
    getRandomTime() {
        return randomInt(1000, 3000)
    }

    //抽奖函数
    async gameDone() {
        try {
            const options = {
                //签到任务调用签到接口
                url: `https://game.dominos.com.cn/abalone/game/gameDone`,
                //请求头, 所有接口通用
                headers: this.headers,
                body: this.body
            };
            //post方法
            let result = await httpRequest(options);
            //console.log(result)
            if (result?.statusCode == 0) {
                //obj.error是0代表完成
                console.log(`✅抽奖成功!获得${result?.content?.name},剩余分享次数:${result?.extra?.sharingNum},今日已抽奖次数:${result?.extra?.doneNum}`);
            } else {
                console.log(`❌${result?.errorMessage}`)
                this.drawStatus = false;
            }
        } catch (e) {
            console.log(e);
        }
    }
    //分享函数
    async sharingDone() {
        try {
            const options = {
                //签到任务调用签到接口
                url: `https://game.dominos.com.cn/abalone/game/sharingDone`,
                //请求头, 所有接口通用
                headers: this.headers,
                body: `${this.openid}&from=1&target=0`
            };
            //post方法
            let result = await httpRequest(options);
            //console.log(result)
            if (result?.statusCode == 0) {
                //obj.error是0代表完成
                console.log(`✅分享成功,抽奖次数+${result?.content?.gameNum}`);
            } else {
                console.log(`❌${result?.errorMessage}`)
                this.sharingStatus = false;
            }
        } catch (e) {
            console.log(e);
        }
    }
    //任务列表
    async todoList() {
        //执行分享，将抽奖次数最大化
        do{
            await this.sharingDone();
            await $.wait(this.getRandomTime());
        }while(this.sharingStatus);
        //循环抽奖，直到使用全部次数
        do{
            await this.gameDone();
            await $.wait(this.getRandomTime());
        }while(this.drawStatus);
        //最后打印奖品信息
        await this.point();
    }
    //查询用户信息
    async point() {
        try {
            const options = {
                //签到任务调用签到接口
                url: `https://game.dominos.com.cn/abalone/game/myPrize?${this.openid}`,
                //请求头, 所有接口通用
                headers: this.headers,
            };
            //post方法
            let result = await httpRequest(options);
            if (result?.statusCode == 0) {
                //obj.error是0代表完成
                let total = getTotal(result?.content);
                DoubleLog(`账号[${result?.extra}] 奖品:`)
                for (let item of total) {
                    DoubleLog(`${giftName[item.name]}x${item.value}`)   
                }
            } else {
                console.log(`❌${result?.errorMessage}`)
                //console.log(result);
            }
        } catch (e) {
            console.log(e);
        }
    }
}
//获取Cookie
async function getCookie() {
    if ($request && $request.method != 'OPTIONS') {
        const tokenValue = $request.body;
        if (tokenValue) {
            $.setdata(tokenValue, ckName);
            $.msg($.name, "", `获取签到Cookie成功🎉\n${tokenValue}`);
        } else {
            $.msg($.name, "", "错误获取签到Cookie失败");
        }
    }
}


//主程序执行入口
!(async () => {
    //没有设置变量,执行Cookie获取
    if (typeof $request != "undefined") {
        await getCookie();
        return;
    }
    //未检测到ck，退出
    if (!(await checkEnv())) { throw new Error(`❌未检测到ck，请添加环境变量`) };
    if (userList.length > 0) {
        await main();
    }
    if ($.barkKey) { //如果已填写Bark Key
        await BarkNotify($, $.barkKey, $.name, $.notifyMsg.join('\n')); //推送Bark通知
    };
})()
    .catch((e) => $.notifyMsg.push(e.message || e))//捕获登录函数等抛出的异常, 并把原因添加到全局变量(通知)
    .finally(async () => {
        await SendMsg($.notifyMsg.join('\n'))//带上总结推送通知
        $.done(); //调用Surge、QX内部特有的函数, 用于退出脚本执行
    });

/** --------------------------------辅助函数区域------------------------------------------- */

// 双平台log输出
function DoubleLog(data) {
    if ($.isNode()) {
        if (data) {
            console.log(`${data}`);
            $.notifyMsg.push(`${data}`);
        }
    } else {
        console.log(`${data}`);
        $.notifyMsg.push(`${data}`);
    }
}

//把json 转为以 '&' 连接的字符串
function toParams(body) {
    var params = Object.keys(body).map(function (key) {
        return encodeURIComponent(key) + "=" + encodeURIComponent(body[key]);
    }).join("&");
    return params;
}

//统计奖品数量
function getTotal(data) {
    let dataContainer = {}; //存分组的
    data.map((item) => {
        //对数据进行遍历
        dataContainer[item.id] = dataContainer[item.id] || [];
        dataContainer[item.id].push(item);
    });
    // console.log(dataContainer);
    let total = [];
    let dataName = Object.keys(dataContainer);
    dataName.map((nameItem) => {
        let count = 0;
        dataContainer[nameItem].map((item) => {
            count++;
        });
        total.push({ name: nameItem, value: count });
    });
    return total;
}

// 示例调用
(async function() {
    // 模拟获取的 data，注意这里传入的是数组
    let data = [
        { id: 1, name: "奖品A" },
        { id: 2, name: "奖品B" },
        { id: 1, name: "奖品A" },
        { id: 3, name: "奖品C" },
        { id: 2, name: "奖品B" }
    ];

    // 调用 UserInfo.point 函数
    try {
        let result = await point(data);
        console.log('最终统计结果:', result);
    } catch (error) {
        console.error('发生错误:', error.message);
    }
})();

//检查变量
async function checkEnv() {
    if (userCookie) {
        // console.log(userCookie);
        let e = envSplitor[0];
        for (let o of envSplitor)
            if (userCookie.indexOf(o) > -1) {
                e = o;
                break;
            }
        for (let n of userCookie.split(e)) n && userList.push(new UserInfo(n));
        userCount = userList.length;
    } else {
        console.log("未找到CK");
        return;
    }
    return console.log(`共找到${userCount}个账号`), true;//true == !0
}

/**
 * 随机整数生成
 */
function randomInt(min, max) {
    return Math.round(Math.random() * (max - min) + min);
}
// 发送消息
async function SendMsg(message) {
    if (!message) return;
    if (Notify > 0) {
        if ($.isNode()) {
            await notify.sendNotify($.name, message)
        } else {
            $.msg($.name, '', message)
        }
    } else {
        console.log(message)
    }
}

/** ---------------------------------固定不动区域----------------------------------------- */
// prettier-ignore

//请求函数函数二次封装
function httpRequest(options, method) { typeof (method) === 'undefined' ? ('body' in options ? method = 'post' : method = 'get') : method = method; return new Promise((resolve) => { $[method](options, (err, resp, data) => { try { if (err) { console.log(`${method}请求失败`); $.logErr(err) } else { if (data) { typeof JSON.parse(data) == 'object' ? data = JSON.parse(data) : data = data; resolve(data) } else { console.log(`请求api返回数据为空，请检查自身原因`) } } } catch (e) { $.logErr(e, resp) } finally { resolve() } }) }) }
//Bark APP notify
async function BarkNotify(c, k, t, b) { for (let i = 0; i < 3; i++) { console.log(`🔷Bark notify >> Start push (${i + 1})`); const s = await new Promise((n) => { c.post({ url: 'https://api.day.app/push', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: t, body: b, device_key: k, ext_params: { group: t } }) }, (e, r, d) => r && r.status == 200 ? n(1) : n(d || e)) }); if (s === 1) { console.log('✅Push success!'); break } else { console.log(`❌Push failed! >> ${s.message || s}`) } } };
//From chavyleung's Env.js
function Env(t, e) { class s { constructor(t) { this.env = t } send(t, e = "GET") { t = "string" == typeof t ? { url: t } : t; let s = this.get; return "POST" === e && (s = this.post), new Promise((e, a) => { s.call(this, t, (t, s, r) => { t ? a(t) : e(s) }) }) } get(t) { return this.send.call(this.env, t) } post(t) { return this.send.call(this.env, t, "POST") } } return new class { constructor(t, e) { this.name = t, this.http = new s(this), this.data = null, this.dataFile = "box.dat", this.logs = [], this.isMute = !1, this.isNeedRewrite = !1, this.logSeparator = "\n", this.encoding = "utf-8", this.startTime = (new Date).getTime(), Object.assign(this, e), this.log("", `🔔${this.name}, 开始!`) } getEnv() { return "undefined" != typeof $environment && $environment["surge-version"] ? "Surge" : "undefined" != typeof $environment && $environment["stash-version"] ? "Stash" : "undefined" != typeof module && module.exports ? "Node.js" : "undefined" != typeof $task ? "Quantumult X" : "undefined" != typeof $loon ? "Loon" : "undefined" != typeof $rocket ? "Shadowrocket" : void 0 } isNode() { return "Node.js" === this.getEnv() } isQuanX() { return "Quantumult X" === this.getEnv() } isSurge() { return "Surge" === this.getEnv() } isLoon() { return "Loon" === this.getEnv() } isShadowrocket() { return "Shadowrocket" === this.getEnv() } isStash() { return "Stash" === this.getEnv() } toObj(t, e = null) { try { return JSON.parse(t) } catch { return e } } toStr(t, e = null) { try { return JSON.stringify(t) } catch { return e } } getjson(t, e) { let s = e; const a = this.getdata(t); if (a) try { s = JSON.parse(this.getdata(t)) } catch { } return s } setjson(t, e) { try { return this.setdata(JSON.stringify(t), e) } catch { return !1 } } getScript(t) { return new Promise(e => { this.get({ url: t }, (t, s, a) => e(a)) }) } runScript(t, e) { return new Promise(s => { let a = this.getdata("@chavy_boxjs_userCfgs.httpapi"); a = a ? a.replace(/\n/g, "").trim() : a; let r = this.getdata("@chavy_boxjs_userCfgs.httpapi_timeout"); r = r ? 1 * r : 20, r = e && e.timeout ? e.timeout : r; const [i, o] = a.split("@"), n = { url: `http://${o}/v1/scripting/evaluate`, body: { script_text: t, mock_type: "cron", timeout: r }, headers: { "X-Key": i, Accept: "*/*" }, timeout: r }; this.post(n, (t, e, a) => s(a)) }).catch(t => this.logErr(t)) } loaddata() { if (!this.isNode()) return {}; { this.fs = this.fs ? this.fs : require("fs"), this.path = this.path ? this.path : require("path"); const t = this.path.resolve(this.dataFile), e = this.path.resolve(process.cwd(), this.dataFile), s = this.fs.existsSync(t), a = !s && this.fs.existsSync(e); if (!s && !a) return {}; { const a = s ? t : e; try { return JSON.parse(this.fs.readFileSync(a)) } catch (t) { return {} } } } } writedata() { if (this.isNode()) { this.fs = this.fs ? this.fs : require("fs"), this.path = this.path ? this.path : require("path"); const t = this.path.resolve(this.dataFile), e = this.path.resolve(process.cwd(), this.dataFile), s = this.fs.existsSync(t), a = !s && this.fs.existsSync(e), r = JSON.stringify(this.data); s ? this.fs.writeFileSync(t, r) : a ? this.fs.writeFileSync(e, r) : this.fs.writeFileSync(t, r) } } lodash_get(t, e, s) { const a = e.replace(/\[(\d+)\]/g, ".$1").split("."); let r = t; for (const t of a) if (r = Object(r)[t], void 0 === r) return s; return r } lodash_set(t, e, s) { return Object(t) !== t ? t : (Array.isArray(e) || (e = e.toString().match(/[^.[\]]+/g) || []), e.slice(0, -1).reduce((t, s, a) => Object(t[s]) === t[s] ? t[s] : t[s] = Math.abs(e[a + 1]) >> 0 == +e[a + 1] ? [] : {}, t)[e[e.length - 1]] = s, t) } getdata(t) { let e = this.getval(t); if (/^@/.test(t)) { const [, s, a] = /^@(.*?)\.(.*?)$/.exec(t), r = s ? this.getval(s) : ""; if (r) try { const t = JSON.parse(r); e = t ? this.lodash_get(t, a, "") : e } catch (t) { e = "" } } return e } setdata(t, e) { let s = !1; if (/^@/.test(e)) { const [, a, r] = /^@(.*?)\.(.*?)$/.exec(e), i = this.getval(a), o = a ? "null" === i ? null : i || "{}" : "{}"; try { const e = JSON.parse(o); this.lodash_set(e, r, t), s = this.setval(JSON.stringify(e), a) } catch (e) { const i = {}; this.lodash_set(i, r, t), s = this.setval(JSON.stringify(i), a) } } else s = this.setval(t, e); return s } getval(t) { switch (this.getEnv()) { case "Surge": case "Loon": case "Stash": case "Shadowrocket": return $persistentStore.read(t); case "Quantumult X": return $prefs.valueForKey(t); case "Node.js": return this.data = this.loaddata(), this.data[t]; default: return this.data && this.data[t] || null } } setval(t, e) { switch (this.getEnv()) { case "Surge": case "Loon": case "Stash": case "Shadowrocket": return $persistentStore.write(t, e); case "Quantumult X": return $prefs.setValueForKey(t, e); case "Node.js": return this.data = this.loaddata(), this.data[e] = t, this.writedata(), !0; default: return this.data && this.data[e] || null } } initGotEnv(t) { this.got = this.got ? this.got : require("got"), this.cktough = this.cktough ? this.cktough : require("tough-cookie"), this.ckjar = this.ckjar ? this.ckjar : new this.cktough.CookieJar, t && (t.headers = t.headers ? t.headers : {}, void 0 === t.headers.Cookie && void 0 === t.cookieJar && (t.cookieJar = this.ckjar)) } get(t, e = (() => { })) { switch (t.headers && (delete t.headers["Content-Type"], delete t.headers["Content-Length"], delete t.headers["content-type"], delete t.headers["content-length"]), t.params && (t.url += "?" + this.queryStr(t.params)), this.getEnv()) { case "Surge": case "Loon": case "Stash": case "Shadowrocket": default: this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, { "X-Surge-Skip-Scripting": !1 })), $httpClient.get(t, (t, s, a) => { !t && s && (s.body = a, s.statusCode = s.status ? s.status : s.statusCode, s.status = s.statusCode), e(t, s, a) }); break; case "Quantumult X": this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, { hints: !1 })), $task.fetch(t).then(t => { const { statusCode: s, statusCode: a, headers: r, body: i, bodyBytes: o } = t; e(null, { status: s, statusCode: a, headers: r, body: i, bodyBytes: o }, i, o) }, t => e(t && t.error || "UndefinedError")); break; case "Node.js": let s = require("iconv-lite"); this.initGotEnv(t), this.got(t).on("redirect", (t, e) => { try { if (t.headers["set-cookie"]) { const s = t.headers["set-cookie"].map(this.cktough.Cookie.parse).toString(); s && this.ckjar.setCookieSync(s, null), e.cookieJar = this.ckjar } } catch (t) { this.logErr(t) } }).then(t => { const { statusCode: a, statusCode: r, headers: i, rawBody: o } = t, n = s.decode(o, this.encoding); e(null, { status: a, statusCode: r, headers: i, rawBody: o, body: n }, n) }, t => { const { message: a, response: r } = t; e(a, r, r && s.decode(r.rawBody, this.encoding)) }) } } post(t, e = (() => { })) { const s = t.method ? t.method.toLocaleLowerCase() : "post"; switch (t.body && t.headers && !t.headers["Content-Type"] && !t.headers["content-type"] && (t.headers["content-type"] = "application/x-www-form-urlencoded"), t.headers && (delete t.headers["Content-Length"], delete t.headers["content-length"]), this.getEnv()) { case "Surge": case "Loon": case "Stash": case "Shadowrocket": default: this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, { "X-Surge-Skip-Scripting": !1 })), $httpClient[s](t, (t, s, a) => { !t && s && (s.body = a, s.statusCode = s.status ? s.status : s.statusCode, s.status = s.statusCode), e(t, s, a) }); break; case "Quantumult X": t.method = s, this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, { hints: !1 })), $task.fetch(t).then(t => { const { statusCode: s, statusCode: a, headers: r, body: i, bodyBytes: o } = t; e(null, { status: s, statusCode: a, headers: r, body: i, bodyBytes: o }, i, o) }, t => e(t && t.error || "UndefinedError")); break; case "Node.js": let a = require("iconv-lite"); this.initGotEnv(t); const { url: r, ...i } = t; this.got[s](r, i).then(t => { const { statusCode: s, statusCode: r, headers: i, rawBody: o } = t, n = a.decode(o, this.encoding); e(null, { status: s, statusCode: r, headers: i, rawBody: o, body: n }, n) }, t => { const { message: s, response: r } = t; e(s, r, r && a.decode(r.rawBody, this.encoding)) }) } } time(t, e = null) { const s = e ? new Date(e) : new Date; let a = { "M+": s.getMonth() + 1, "d+": s.getDate(), "H+": s.getHours(), "m+": s.getMinutes(), "s+": s.getSeconds(), "q+": Math.floor((s.getMonth() + 3) / 3), S: s.getMilliseconds() }; /(y+)/.test(t) && (t = t.replace(RegExp.$1, (s.getFullYear() + "").substr(4 - RegExp.$1.length))); for (let e in a) new RegExp("(" + e + ")").test(t) && (t = t.replace(RegExp.$1, 1 == RegExp.$1.length ? a[e] : ("00" + a[e]).substr(("" + a[e]).length))); return t } queryStr(t) { let e = ""; for (const s in t) { let a = t[s]; null != a && "" !== a && ("object" == typeof a && (a = JSON.stringify(a)), e += `${s}=${a}&`) } return e = e.substring(0, e.length - 1), e } msg(e = t, s = "", a = "", r) { const i = t => { switch (typeof t) { case void 0: return t; case "string": switch (this.getEnv()) { case "Surge": case "Stash": default: return { url: t }; case "Loon": case "Shadowrocket": return t; case "Quantumult X": return { "open-url": t }; case "Node.js": return }case "object": switch (this.getEnv()) { case "Surge": case "Stash": case "Shadowrocket": default: { let e = t.url || t.openUrl || t["open-url"]; return { url: e } } case "Loon": { let e = t.openUrl || t.url || t["open-url"], s = t.mediaUrl || t["media-url"]; return { openUrl: e, mediaUrl: s } } case "Quantumult X": { let e = t["open-url"] || t.url || t.openUrl, s = t["media-url"] || t.mediaUrl, a = t["update-pasteboard"] || t.updatePasteboard; return { "open-url": e, "media-url": s, "update-pasteboard": a } } case "Node.js": return }default: return } }; if (!this.isMute) switch (this.getEnv()) { case "Surge": case "Loon": case "Stash": case "Shadowrocket": default: $notification.post(e, s, a, i(r)); break; case "Quantumult X": $notify(e, s, a, i(r)); break; case "Node.js": }if (!this.isMuteLog) { let t = ["", "==============📣系统通知📣=============="]; t.push(e), s && t.push(s), a && t.push(a), console.log(t.join("\n")), this.logs = this.logs.concat(t) } } log(...t) { t.length > 0 && (this.logs = [...this.logs, ...t]), console.log(t.join(this.logSeparator)) } logErr(t, e) { switch (this.getEnv()) { case "Surge": case "Loon": case "Stash": case "Shadowrocket": case "Quantumult X": default: this.log("", `❗️${this.name}, 错误!`, t); break; case "Node.js": this.log("", `❗️${this.name}, 错误!`, t.stack) } } wait(t) { return new Promise(e => setTimeout(e, t)) } done(t = {}) { const e = (new Date).getTime(), s = (e - this.startTime) / 1e3; switch (this.log("", `🔔${this.name}, 结束! 🕛 ${s} 秒`), this.log(), this.getEnv()) { case "Surge": case "Loon": case "Stash": case "Shadowrocket": case "Quantumult X": default: $done(t); break; case "Node.js": process.exit(1) } } }(t, e) }
