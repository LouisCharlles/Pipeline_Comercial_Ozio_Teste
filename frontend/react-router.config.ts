import type { Config } from "@react-router/dev/config";

export default {
  appDirectory: "app",
  // A listagem precisa chegar pronta do servidor (FR-017).
  ssr: true,
} satisfies Config;
