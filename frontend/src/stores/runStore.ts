import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type RunStatus = 'idle' | 'running' | 'achieved' | 'failed' | 'aborted'

export interface RunState {
  runId: string
  goal: string
  status: RunStatus
  iteration: number
  maxIterations: number
  modelName: string
  goalReason: string
  hitlEnabled: boolean
  cwd: string
}

export const useRunStore = defineStore('run', () => {
  const activeRun = ref<RunState | null>(null)
  const allRuns = ref<RunState[]>([])

  const isRunning = computed(() => activeRun.value?.status === 'running')
  const awaitingHuman = ref(false)

  function setActiveRun(run: RunState) {
    activeRun.value = run
    const idx = allRuns.value.findIndex((r) => r.runId === run.runId)
    if (idx >= 0) allRuns.value[idx] = run
    else allRuns.value.unshift(run)
  }

  function updateStatus(runId: string, status: RunStatus, reason?: string) {
    if (activeRun.value?.runId === runId) {
      activeRun.value.status = status
      if (reason !== undefined) activeRun.value.goalReason = reason
    }
    const run = allRuns.value.find((r) => r.runId === runId)
    if (run) {
      run.status = status
      if (reason !== undefined) run.goalReason = reason
    }
  }

  function updateIteration(runId: string, iteration: number) {
    if (activeRun.value?.runId === runId) {
      activeRun.value.iteration = iteration
    }
  }

  function setAwaitingHuman(val: boolean) {
    awaitingHuman.value = val
  }

  function clearActive() {
    activeRun.value = null
    awaitingHuman.value = false
  }

  return {
    activeRun,
    allRuns,
    isRunning,
    awaitingHuman,
    setActiveRun,
    updateStatus,
    updateIteration,
    setAwaitingHuman,
    clearActive,
  }
})
