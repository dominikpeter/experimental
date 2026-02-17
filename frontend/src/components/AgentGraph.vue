<script setup lang="ts">
import { computed } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { useEventStore } from '@/stores/eventStore'
import { useRunStore } from '@/stores/runStore'
import type { Node, Edge } from '@vue-flow/core'

const eventStore = useEventStore()
const runStore = useRunStore()

// Determine active node from most recent step_start event
const activeNode = computed(() => {
  const run = runStore.activeRun
  if (!run) return null
  const stepEvents = eventStore.events
    .filter((e) => e.run_id === run.runId && e.kind === 'step_start')
  if (stepEvents.length === 0) return null
  return stepEvents[stepEvents.length - 1].payload.node as string
})

const nodeStyle = (id: string) => {
  const isActive = activeNode.value === id
  const isEnd = id === 'end'
  return {
    background: isEnd
      ? 'rgba(100,116,139,0.2)'
      : isActive
        ? 'rgba(124,58,237,0.4)'
        : 'rgba(15,10,46,0.8)',
    border: `2px solid ${isActive ? '#a78bfa' : isEnd ? '#64748b' : 'rgba(124,58,237,0.4)'}`,
    color: '#e2e8f0',
    borderRadius: '10px',
    padding: '10px 18px',
    fontFamily: 'system-ui, sans-serif',
    fontSize: '13px',
    fontWeight: isActive ? '700' : '500',
    boxShadow: isActive ? '0 0 20px rgba(124,58,237,0.6)' : 'none',
    transition: 'all 0.3s ease',
  }
}

const nodes = computed<Node[]>(() => [
  { id: 'start', type: 'input', position: { x: 250, y: 20 }, label: '▶ START', style: nodeStyle('start') },
  { id: 'plan', position: { x: 220, y: 110 }, label: '🧠 plan', style: nodeStyle('plan') },
  { id: 'act', position: { x: 380, y: 200 }, label: '⚡ act', style: nodeStyle('act') },
  { id: 'evaluate', position: { x: 220, y: 290 }, label: '🔍 evaluate', style: nodeStyle('evaluate') },
  { id: 'human_check', position: { x: 60, y: 380 }, label: '👤 human check', style: nodeStyle('human_check') },
  { id: 'end', type: 'output', position: { x: 250, y: 480 }, label: '■ END', style: nodeStyle('end') },
])

const edges = computed<Edge[]>(() => [
  { id: 'e-start-plan', source: 'start', target: 'plan', animated: activeNode.value === 'plan' },
  { id: 'e-plan-act', source: 'plan', target: 'act', label: 'has tools', animated: activeNode.value === 'act' },
  { id: 'e-plan-eval', source: 'plan', target: 'evaluate', label: 'no tools', animated: false },
  { id: 'e-act-eval', source: 'act', target: 'evaluate', animated: activeNode.value === 'evaluate' },
  { id: 'e-eval-plan', source: 'evaluate', target: 'plan', label: 'continue', animated: activeNode.value === 'plan' },
  { id: 'e-eval-hitl', source: 'evaluate', target: 'human_check', label: 'hitl', animated: activeNode.value === 'human_check' },
  { id: 'e-eval-end', source: 'evaluate', target: 'end', label: 'done', animated: false },
  { id: 'e-hitl-plan', source: 'human_check', target: 'plan', label: 'approve', animated: false },
  { id: 'e-hitl-end', source: 'human_check', target: 'end', label: 'abort', animated: false },
])
</script>

<template>
  <div class="agent-graph">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :edges-updatable="false"
      :nodes-draggable="false"
      :nodes-connectable="false"
      :zoom-on-scroll="false"
      :pan-on-drag="false"
      fit-view-on-init
      class="flow"
    >
      <Background pattern-color="rgba(124,58,237,0.1)" :gap="20" />
    </VueFlow>
  </div>
</template>

<style scoped>
.agent-graph {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  backdrop-filter: blur(12px);
  height: 100%;
}

.flow {
  width: 100%;
  height: 100%;
}

:deep(.vue-flow__edge-path) {
  stroke: rgba(124, 58, 237, 0.5);
  stroke-width: 2;
}
:deep(.vue-flow__edge.animated .vue-flow__edge-path) {
  stroke: #a78bfa;
}
:deep(.vue-flow__edge-label) {
  font-size: 11px;
  fill: #94a3b8;
  background: transparent;
}
</style>
