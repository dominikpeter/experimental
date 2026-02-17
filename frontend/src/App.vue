<script setup lang="ts">
import RunControls from '@/components/RunControls.vue'
import GoalStatus from '@/components/GoalStatus.vue'
import EventLog from '@/components/EventLog.vue'
import AgentGraph from '@/components/AgentGraph.vue'
import HumanCheckModal from '@/components/HumanCheckModal.vue'
</script>

<template>
  <div class="app">
    <!-- Header -->
    <header class="app-header">
      <div class="logo">
        <span class="logo-re">retr</span><span class="logo-ai">AI</span>
      </div>
      <p class="tagline">Self-solving AI agent loop</p>
    </header>

    <!-- Main layout -->
    <main class="app-main">
      <!-- Left sidebar -->
      <aside class="sidebar">
        <RunControls />
        <GoalStatus />
      </aside>

      <!-- Graph panel -->
      <section class="graph-panel">
        <AgentGraph />
      </section>

      <!-- Log panel -->
      <section class="log-panel">
        <EventLog />
      </section>
    </main>

    <!-- HITL modal (portal) -->
    <HumanCheckModal />
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: baseline;
  gap: 1rem;
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--color-border);
  background: rgba(26, 5, 51, 0.6);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.logo-re {
  background: linear-gradient(135deg, #a78bfa, #7c3aed);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-ai {
  background: linear-gradient(135deg, #7c3aed, #1e1b4b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tagline {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.app-main {
  flex: 1;
  display: grid;
  grid-template-columns: 320px 1fr 1fr;
  grid-template-rows: calc(100vh - 65px);
  gap: 1rem;
  padding: 1rem;
  overflow: hidden;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.graph-panel {
  min-height: 0;
}

.log-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
</style>
