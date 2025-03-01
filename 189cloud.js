/*
    name: "天翼云盘签到"
    cron: 0 0,8 * * *
    更新时间:2025-03-01
*/
// 变量TY_ACCOUNTS=手机号 密码 家庭;手机号 密码 家庭
// 参数之间用空格分隔,账号间用:分隔
// 不记得账号密码的去https://cloud.189.cn/ 登录或者修改
// 家庭id默认是家庭主账号的手机号,如果不是或者修改过,请到天翼云app -文件 -家庭共享 - 右上角家庭id点进去编辑
const fs = require("fs");
const { Cookie, CookieJar } = require("tough-cookie");
const { CloudClient } = require("cloud189-sdk");

// 从环境变量中获取设置
const execThreshold = process.env.EXEC_THRESHOLD || 1;
const cacheCookie = process.env.CACHE_COOKIE === "true";  // 从环境变量读取缓存设置
const accountsEnv = process.env.TY_ACCOUNTS || "";  // 从环境变量读取账号信息

// 解析账号信息
const accounts = accountsEnv.split(";").map(account => {
  const [userName, password, familyId] = account.split(" ");
  return { userName, password, familyId };
});

// 个人任务签到
const doUserTask = async (cloudClient, logger) => {
  const tasks = Array.from({ length: execThreshold }, () =>
    cloudClient.userSign()
  );
  const result = (await Promise.all(tasks)).filter((res) => !res.isSign);
  logger.info(
    `个人签到任务: 成功数/总请求数 ${result.length}/${tasks.length} 获得 ${
      result.map((res) => res.netdiskBonus)?.join(",") || "0"
    }M 空间`
  );
};

// 直接通过环境变量设置家庭组
const families = JSON.parse(process.env.TY_FAMILIES || "[]");

// 家庭任务签到
const doFamilyTask = async (cloudClient, logger) => {
  const { familyInfoResp } = await cloudClient.getFamilyList();
  if (familyInfoResp) {
    let familyId = null;
    // 指定家庭签到
    if (families.length > 0) {
      const targetFamily = familyInfoResp.find((familyInfo) =>
        families.includes(familyInfo.remarkName)
      );
      if (targetFamily) {
        familyId = targetFamily.familyId;
      } else {
        logger.error(
          `没有加入到指定家庭分组${families
            .map((family) => mask(family, 3, 7))
            .toString()}`
        );
      }
    } else {
      familyId = familyInfoResp[0].familyId;
    }
    logger.info(`执行家庭签到ID:${familyId}`);
    const tasks = Array.from({ length: execThreshold }, () =>
      cloudClient.familyUserSign(familyId)
    );
    const result = (await Promise.all(tasks)).filter((res) => !res.signStatus);
    return logger.info(
      `家庭签到任务: 成功数/总请求数 ${result.length}/${tasks.length} 获得 ${
        result.map((res) => res.bonusSpace)?.join(",") || "0"
      }M 空间`
    );
  }
};



const cookieDir = `.cookie/${new Date().toISOString().slice(0, 10)}`;

const saveCookies = async (userName, cookieJar) => {
  const ipIpAddr = await getIpAddr();
  if (!ipIpAddr) {
    return;
  }
  deleteNonTargetDirectories(".cookie", new Date().toISOString().slice(0, 10));
  const cookiePath = `${cookieDir}/${ipIpAddr}`;
  if (!fs.existsSync(cookiePath)) {
    fs.mkdirSync(cookiePath, { recursive: true });
  }
  const cookies = cookieJar
    .getCookiesSync("https://cloud.189.cn")
    .map((cookie) => cookie.toString());
  fs.writeFileSync(`${cookiePath}/${userName}.json`, JSON.stringify(cookies), {
    encoding: "utf-8",
  });
};

const loadCookies = async (userName) => {
  const ipIpAddr = await getIpAddr();
  if (!ipIpAddr) {
    return;
  }
  const cookiePath = `${cookieDir}/${ipIpAddr}`;
  if (fs.existsSync(`${cookiePath}/${userName}.json`)) {
    const cookies = JSON.parse(
      fs.readFileSync(`${cookiePath}/${userName}.json`, { encoding: "utf8" })
    );
    const cookieJar = new CookieJar();
    cookies.forEach((cookie) => {
      cookieJar.setCookieSync(Cookie.parse(cookie), "https://cloud.189.cn");
    });
    return cookieJar;
  }
  return null;
};

// 获取 IP 地址
const getIpAddr = async () => {
  try {
    const os = require("os");
    const interfaces = os.networkInterfaces();
    for (const iface in interfaces) {
      for (const addr of interfaces[iface]) {
        if (addr.family === 'IPv4' && !addr.internal) {
          return addr.address;
        }
      }
    }
  } catch (err) {
    console.error("获取IP地址失败:", err);
  }
  return null;
};

// 删除不需要的目录
const deleteNonTargetDirectories = (dir, targetDate) => {
  fs.readdirSync(dir).forEach((folder) => {
    if (!folder.includes(targetDate)) {
      const fullPath = `${dir}/${folder}`;
      fs.rmSync(fullPath, { recursive: true, force: true });
    }
  });
};

// 延迟函数
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 将数组分批
const groupByNum = (arr, num) => {
  const result = [];
  for (let i = 0; i < arr.length; i += num) {
    result.push(arr.slice(i, i + num));
  }
  return result;
};

const run = async (userName, password, familyId, userSizeInfoMap, logger) => {
  if (userName && password) {
    const before = Date.now();
    try {
      logger.log(`开始执行`);
      const cloudClient = new CloudClient(userName, password);
      if (cacheCookie) {
        const cookies = await loadCookies(userName);
        if (cookies) {
          cloudClient.cookieJar = cookies;
        } else {
          await cloudClient.login();
          await saveCookies(userName, cloudClient.cookieJar);
        }
      } else {
        await cloudClient.login();
      }
      const beforeUserSizeInfo = await cloudClient.getUserSizeInfo();
      userSizeInfoMap.set(userName, {
        cloudClient,
        userSizeInfo: beforeUserSizeInfo,
      });
      await Promise.all([doUserTask(cloudClient, logger), doFamilyTask(cloudClient, logger, familyId)]);
    } catch (e) {
      if (e.response) {
        logger.log(`请求失败: ${e.response.statusCode}, ${e.response.body}`);
      } else {
        logger.error(e);
      }
      if (e.code === "ECONNRESET" || e.code === "ETIMEDOUT") {
        logger.error("请求超时");
        throw e;
      }
    } finally {
      logger.log(
        `执行完毕, 耗时 ${((Date.now() - before) / 1000).toFixed(2)} 秒`
      );
    }
  }
};

// 开始执行程序
async function main() {
  //用于统计实际容量变化
  const userSizeInfoMap = new Map();
  //分批执行
  const groupMaxNum = 5;
  const runTaskGroups = groupByNum(accounts, groupMaxNum);
  for (let index = 0; index < runTaskGroups.length; index++) {
    const taskGroup = runTaskGroups[index];
    await Promise.all(
      taskGroup.map((account) => {
        const { userName, password, familyId } = account;
        const logger = console;  // 直接使用console进行日志记录
        return run(userName, password, familyId, userSizeInfoMap, logger);
      })
    );
  }

  // 数据汇总
  for (const [userName, { cloudClient, userSizeInfo }] of userSizeInfoMap) {
    const afterUserSizeInfo = await cloudClient.getUserSizeInfo();
    const logger = console;  // 直接使用console进行日志记录
    logger.log(
      `个人总容量增加：${(
        (afterUserSizeInfo.cloudCapacityInfo.totalSize -
          userSizeInfo.cloudCapacityInfo.totalSize) /
        1024 /
        1024
      ).toFixed(2)}M,家庭容量增加：${(
        (afterUserSizeInfo.familyCapacityInfo.totalSize -
          userSizeInfo.familyCapacityInfo.totalSize) /
        1024 /
        1024
      ).toFixed(2)}M`
    );
  }
}

(async () => {
  try {
    await main();
    //等待日志文件写入
    await delay(1000);
  } finally {
    console.log('任务完成');
  }
})();
