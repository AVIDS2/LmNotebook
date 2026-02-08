<template>
  <section class="startup-page">
    <div class="startup-page__hero">
      <div class="startup-page__badge">Origin Notes</div>
      <h1 class="startup-page__title">{{ t('startup.title') }}</h1>
      <p class="startup-page__subtitle">{{ t('startup.subtitle') }}</p>
      <div class="startup-page__cta">
        <button class="startup-page__btn startup-page__btn--primary" @click="$emit('create-first-note')">
          {{ t('startup.quickStart') }}
        </button>
        <button class="startup-page__btn" @click="$emit('import-backup')">
          {{ t('startup.importBackup') }}
        </button>
        <button class="startup-page__btn" @click="$emit('open-data-directory')">
          {{ t('startup.openDataDirectory') }}
        </button>
      </div>
    </div>

    <div class="startup-page__panel">
      <div class="startup-page__stats">
        <div class="startup-page__stat">
          <span class="startup-page__stat-label">{{ t('startup.stats.notes') }}</span>
          <strong class="startup-page__stat-value">{{ noteCount }}</strong>
        </div>
        <div class="startup-page__stat">
          <span class="startup-page__stat-label">{{ t('startup.stats.categories') }}</span>
          <strong class="startup-page__stat-value">{{ categoryCount }}</strong>
        </div>
        <div class="startup-page__stat">
          <span class="startup-page__stat-label">{{ t('startup.stats.mode') }}</span>
          <strong class="startup-page__stat-value">{{ t('startup.stats.localFirst') }}</strong>
        </div>
      </div>

      <div class="startup-page__feature-grid">
        <article class="startup-page__feature">
          <h3>{{ t('startup.features.editor.title') }}</h3>
          <p>{{ t('startup.features.editor.desc') }}</p>
        </article>
        <article class="startup-page__feature">
          <h3>{{ t('startup.features.search.title') }}</h3>
          <p>{{ t('startup.features.search.desc') }}</p>
        </article>
        <article class="startup-page__feature">
          <h3>{{ t('startup.features.agent.title') }}</h3>
          <p>{{ t('startup.features.agent.desc') }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from '@/i18n'

defineProps<{
  noteCount: number
  categoryCount: number
}>()

defineEmits<{
  'create-first-note': []
  'import-backup': []
  'open-data-directory': []
}>()

const { t } = useI18n()
</script>

<style scoped lang="scss">
.startup-page {
  display: grid;
  grid-template-rows: auto auto;
  gap: 20px;
  width: min(1080px, calc(100vw - 48px));
  margin: 0 auto;
  padding: 28px 0 20px;
}

.startup-page__hero {
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  background:
    radial-gradient(1200px 300px at -5% -40%, color-mix(in srgb, var(--color-accent) 16%, transparent), transparent),
    var(--color-bg-card);
  padding: 28px;
}

.startup-page__badge {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 12px;
  letter-spacing: 0.04em;
}

.startup-page__title {
  margin-top: 14px;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.15;
  color: var(--color-text-primary);
}

.startup-page__subtitle {
  margin-top: 10px;
  max-width: 760px;
  color: var(--color-text-secondary);
  font-size: 15px;
  line-height: 1.65;
}

.startup-page__cta {
  margin-top: 22px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.startup-page__btn {
  height: 40px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid var(--color-border-dark);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.12s ease, background-color 0.16s ease;

  &:hover {
    background: var(--color-bg-hover);
  }

  &:active {
    transform: translateY(1px);
  }
}

.startup-page__btn--primary {
  border-color: transparent;
  background: linear-gradient(90deg, color-mix(in srgb, var(--color-accent) 84%, #fff 16%), var(--color-accent));
  color: #fff;

  &:hover {
    background: linear-gradient(90deg, var(--color-accent), color-mix(in srgb, var(--color-accent) 88%, #000 12%));
  }

  &:active {
    background: var(--color-accent);
  }
}

.startup-page__panel {
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  background: var(--color-bg-card);
  padding: 20px;
}

.startup-page__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.startup-page__stat {
  border: 1px solid var(--color-border-light);
  border-radius: 12px;
  padding: 12px 14px;
  background: var(--color-bg-primary);
}

.startup-page__stat-label {
  display: block;
  font-size: 12px;
  color: var(--color-text-muted);
}

.startup-page__stat-value {
  margin-top: 5px;
  display: block;
  font-size: 22px;
  color: var(--color-text-primary);
}

.startup-page__feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.startup-page__feature {
  border: 1px solid var(--color-border-light);
  border-radius: 12px;
  background: var(--color-bg-primary);
  padding: 14px;

  h3 {
    font-size: 14px;
    color: var(--color-text-primary);
  }

  p {
    margin-top: 6px;
    font-size: 13px;
    line-height: 1.6;
    color: var(--color-text-secondary);
  }
}

@media (max-width: 960px) {
  .startup-page {
    width: calc(100vw - 28px);
    padding-top: 16px;
  }

  .startup-page__stats,
  .startup-page__feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
