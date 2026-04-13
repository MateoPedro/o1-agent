import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchInbox, fetchPipeline, createPlan, toggleTodo, sendEmail, acceptOpportunity, logEvidence, fetchEvidence } from "./api"

export function useInbox(limit = 10) {
  return useQuery({
    queryKey: ["inbox", limit],
    queryFn: () => fetchInbox(limit),
    refetchInterval: 60_000,
  })
}

export function usePipeline() {
  return useQuery({
    queryKey: ["pipeline"],
    queryFn: fetchPipeline,
    refetchInterval: 60_000,
  })
}

export function useCreatePlan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inbox"] })
      queryClient.invalidateQueries({ queryKey: ["pipeline"] })
    },
  })
}

export function useSendEmail() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ draftId, emailId }: { draftId: number; emailId: string }) =>
      sendEmail(draftId, emailId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipeline"] })
    },
  })
}

export function useEvidence() {
  return useQuery({ queryKey: ["evidence"], queryFn: fetchEvidence })
}

export function useAcceptOpportunity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: acceptOpportunity,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pipeline"] }),
  })
}

export function useLogEvidence() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: logEvidence,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipeline"] })
      queryClient.invalidateQueries({ queryKey: ["evidence"] })
    },
  })
}

export function useToggleTodo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ draftId, todoId }: { draftId: number; todoId: string }) =>
      toggleTodo(draftId, todoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipeline"] })
    },
  })
}
