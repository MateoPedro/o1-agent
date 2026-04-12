import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchInbox, approveOpportunity } from "./api"

export function useInbox(limit = 10) {
  return useQuery({
    queryKey: ["inbox", limit],
    queryFn: () => fetchInbox(limit),
    refetchInterval: 60_000, // auto-refresh every minute
  })
}

export function useApproveOpportunity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: approveOpportunity,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inbox"] })
    },
  })
}
