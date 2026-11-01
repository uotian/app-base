"use client";

import { useQuery } from "@tanstack/react-query";
import type { StatusData } from "@/types/status";
import { getEnvironment, getGreeting } from "@/utils/runtime";

export function useStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: async ({ signal }): Promise<StatusData> => {
      const [environment, greeting] = await Promise.all([
        getEnvironment(),
        getGreeting(signal),
      ]);
      return { environment: environment.message, greeting: greeting.message };
    },
  });
}
