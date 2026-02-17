import { ref, onUnmounted } from 'vue'
import { useRunStore } from '@/stores/runStore'
import { useEventStore } from '@/stores/eventStore'

export function useWebSocket(runId: string) {
  const runStore = useRunStore()
  const eventStore = useEventStore()
  const connected = ref(false)
  const error = ref<string | null>(null)
  let ws: WebSocket | null = null

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/api/ws/${runId}`

    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      error.value = null
    }

    ws.onmessage = (evt) => {
      let data: Record<string, unknown>
      try {
        data = JSON.parse(evt.data)
      } catch {
        return
      }

      const event = data as {
        kind: string
        run_id: string
        iteration: number
        payload: Record<string, unknown>
        ts: number
      }

      // Dispatch to event store
      eventStore.addEvent({
        kind: event.kind as never,
        run_id: event.run_id,
        iteration: event.iteration,
        payload: event.payload,
        ts: event.ts,
      })

      // Update run store based on event kind
      handleEvent(event)
    }

    ws.onerror = () => {
      error.value = 'WebSocket error'
      connected.value = false
    }

    ws.onclose = () => {
      connected.value = false
    }
  }

  function handleEvent(event: Record<string, unknown>) {
    const kind = event.kind as string
    const payload = (event.payload || {}) as Record<string, unknown>
    const iteration = event.iteration as number

    if (kind === 'iteration_complete') {
      runStore.updateIteration(runId, iteration)
    } else if (kind === 'goal_check') {
      const reason = payload.reason as string
      const achieved = payload.achieved as boolean
      if (achieved) {
        runStore.updateStatus(runId, 'achieved', reason)
      }
    } else if (kind === 'human_check_required') {
      runStore.setAwaitingHuman(true)
    } else if (kind === 'human_check_response') {
      runStore.setAwaitingHuman(false)
    } else if (kind === 'run_end') {
      const status = payload.status as string
      const reason = payload.reason as string
      runStore.updateStatus(
        runId,
        status === 'achieved' ? 'achieved' : 'failed',
        reason,
      )
      runStore.setAwaitingHuman(false)
    } else if (kind === 'error') {
      runStore.updateStatus(runId, 'failed', payload.error as string)
    }
  }

  function disconnect() {
    ws?.close()
    ws = null
  }

  onUnmounted(disconnect)

  return { connected, error, connect, disconnect }
}
