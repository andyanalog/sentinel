/**
 * Bot simulator — hammers a target URL at N rps from a spoofed IP.
 * Usage: ts-node --esm bot.ts --target=http://localhost:3000 --rps=20 --duration=15
 */

const args = Object.fromEntries(
  process.argv
    .slice(2)
    .filter((a) => a.startsWith("--"))
    .map((a) => {
      const [k, v] = a.replace(/^--/, "").split("=");
      return [k, v ?? "true"];
    }),
) as Record<string, string>;

const target = args.target ?? "http://localhost:3000";
const rps = Number(args.rps ?? "20");
const durationSec = Number(args.duration ?? "15");
const botIp = args.ip ?? "185.220.1.42";

const headers = {
  "x-forwarded-for": botIp,
  "user-agent": "BurstBot/1.0",
  "content-type": "application/json",
};

let sent = 0;
let blocked = 0;
let allowed = 0;

async function fire() {
  sent++;
  try {
    const resp = await fetch(`${target}/api/submit`, {
      method: "POST",
      headers,
      body: JSON.stringify({ data: "spam" }),
    });
    if (resp.status === 429) blocked++;
    else if (resp.ok) allowed++;
  } catch {
    // network hiccup — ignore
  }
}

console.log(`bot → ${target} @ ${rps} rps for ${durationSec}s (ip=${botIp})`);
const intervalMs = 1000 / rps;
const deadline = Date.now() + durationSec * 1000;
const timer = setInterval(() => {
  if (Date.now() > deadline) {
    clearInterval(timer);
    setTimeout(() => {
      console.log(`sent=${sent} allowed=${allowed} blocked=${blocked}`);
      process.exit(0);
    }, 500);
    return;
  }
  fire();
}, intervalMs);
