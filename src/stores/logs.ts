import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface CommandLog {
  id: string;
  timestamp: Date;
  command: string;
  tool: string; // 'dig', 'curl', 'whois', etc.
  args: string[];
  output: string;
  exitCode: number;
  duration: number; // in milliseconds
  domain?: string;
}

export const useLogsStore = defineStore('logs', () => {
  // State
  const logs = ref<CommandLog[]>([]);

  // Actions
  const addLog = (log: Omit<CommandLog, 'id' | 'timestamp'>) => {
    const newLog: CommandLog = {
      ...log,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    logs.value.unshift(newLog); // Add to beginning for most recent first
  };

  const clearLogs = () => {
    logs.value.splice(0, logs.value.length);
  };

  const getLogsByDomain = (domain: string) => {
    return logs.value.filter((log) => log.domain === domain);
  };

  const getLogsByTool = (tool: string) => {
    return logs.value.filter((log) => log.tool === tool);
  };

  return {
    logs,
    addLog,
    clearLogs,
    getLogsByDomain,
    getLogsByTool,
  };
});
