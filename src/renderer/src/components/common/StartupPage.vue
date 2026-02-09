<template>
  <section class="startup-page">
    <div class="startup-page__hero">
      <div class="startup-page__hero-main">
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

      <aside class="startup-page__hero-side">
        <div class="startup-page__metric">
          <span class="startup-page__metric-label">{{ t('startup.stats.notes') }}</span>
          <strong class="startup-page__metric-value">{{ noteCount }}</strong>
        </div>
        <div class="startup-page__metric">
          <span class="startup-page__metric-label">{{ t('startup.stats.categories') }}</span>
          <strong class="startup-page__metric-value">{{ categoryCount }}</strong>
        </div>
        <div class="startup-page__metric">
          <span class="startup-page__metric-label">{{ t('startup.stats.mode') }}</span>
          <strong class="startup-page__metric-value startup-page__metric-value--mode">
            {{ t('startup.stats.localFirst') }}
          </strong>
        </div>
      </aside>
    </div>

    <div class="startup-page__panel">
      <div class="startup-page__feature-grid">
        <article class="startup-page__feature startup-page__feature--wide">
          <h3>{{ t('startup.features.editor.title') }}</h3>
          <p>{{ t('startup.features.editor.desc') }}</p>
        </article>
        <article class="startup-page__feature">
          <h3>{{ t('startup.features.search.title') }}</h3>
          <p>{{ t('startup.features.search.desc') }}</p>
        </article>
        <article class="startup-page__feature startup-page__feature--accent">
          <h3>{{ t('startup.features.agent.title') }}</h3>
          <p>{{ t('startup.features.agent.desc') }}</p>
        </article>
      </div>

      <div class="startup-page__footnote">
        <span class="startup-page__footnote-line"></span>
        <span class="startup-page__footnote-text">Origin Notes</span>
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
  --gold-1: #b77145;
  --gold-2: #e0b175;
  --gold-3: #8a5e41;
  display: grid;
  gap: clamp(14px, 2.4vh, 24px);
  width: min(1240px, calc(100vw - 48px));
  margin: 0 auto;
  padding: clamp(16px, 2.6vh, 34px) 0 clamp(18px, 3vh, 30px);
  min-height: 100%;
  align-content: start;
  overflow: hidden;
}

.startup-page__hero {
  border: 1px solid color-mix(in srgb, var(--color-border) 70%, #ffffff 30%);
  border-radius: 18px;
  background:
    radial-gradient(1200px 380px at -15% -65%, color-mix(in srgb, var(--color-accent) 18%, transparent), transparent),
    radial-gradient(800px 220px at 90% 120%, color-mix(in srgb, var(--color-accent) 12%, transparent), transparent),
    var(--color-bg-card);
  padding: clamp(18px, 3vw, 34px);
  display: grid;
  gap: clamp(16px, 2vw, 28px);
  grid-template-columns: minmax(0, 1fr) minmax(230px, 300px);
  align-items: stretch;
}

.startup-page__hero-main {
  min-width: 0;
}

.startup-page__hero-side {
  border-left: 1px solid color-mix(in srgb, var(--color-border-light) 78%, transparent);
  padding-left: clamp(14px, 1.8vw, 22px);
  display: grid;
  align-content: center;
  gap: 10px;
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
  font-size: clamp(30px, 4vw, 58px);
  line-height: 1.08;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
  max-width: 18ch;
}

.startup-page__subtitle {
  margin-top: 12px;
  max-width: 56ch;
  color: var(--color-text-secondary);
  font-size: clamp(14px, 1.2vw, 20px);
  line-height: 1.7;
}

.startup-page__cta {
  margin-top: clamp(18px, 2.2vw, 28px);
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.startup-page__btn {
  min-height: 42px;
  padding: 10px 16px;
  border-radius: 12px;
  border: 1px solid var(--color-border-dark);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.14s ease, background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;

  &:hover {
    background: var(--color-bg-hover);
    border-color: color-mix(in srgb, var(--color-border-dark) 65%, var(--color-accent) 35%);
  }

  &:active {
    transform: translateY(1px);
  }
}

.startup-page__btn--primary {
  border-color: transparent;
  background: linear-gradient(110deg, var(--gold-1), var(--gold-2), var(--gold-3), var(--gold-2));
  background-size: 220% 220%;
  animation: startup-gold-flow 8s ease-in-out infinite;
  color: #fff;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--color-accent) 30%, transparent);

  &:hover {
    background: linear-gradient(110deg, var(--gold-1), var(--gold-2), var(--gold-3), var(--gold-2));
    background-size: 220% 220%;
    color: #fff;
    border-color: transparent;
    filter: saturate(1.06);
  }

  &:active {
    background: var(--color-accent);
  }
}

.startup-page__panel {
  border: 1px solid color-mix(in srgb, var(--color-border) 70%, #fff 30%);
  border-radius: 18px;
  background: var(--color-bg-card);
  padding: clamp(14px, 2vw, 24px);
}

.startup-page__metric {
  border: 1px solid color-mix(in srgb, var(--color-border-light) 88%, transparent);
  border-radius: 12px;
  padding: 12px 14px;
  background: var(--color-bg-primary);
}

.startup-page__metric-label {
  display: block;
  font-size: 12px;
  letter-spacing: 0.03em;
  color: var(--color-text-muted);
}

.startup-page__metric-value {
  margin-top: 6px;
  display: block;
  font-size: clamp(24px, 2vw, 34px);
  line-height: 1.12;
  color: var(--color-text-primary);
}

.startup-page__metric-value--mode {
  font-size: clamp(24px, 1.9vw, 30px);
  background: linear-gradient(115deg, var(--gold-1), var(--gold-2), var(--gold-3), var(--gold-2));
  background-size: 220% 220%;
  animation: startup-gold-flow 8s ease-in-out infinite;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.startup-page__feature-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.startup-page__feature {
  border: 1px solid color-mix(in srgb, var(--color-border-light) 88%, transparent);
  border-radius: 12px;
  background: var(--color-bg-primary);
  padding: 16px;
  grid-column: span 2;

  h3 {
    font-size: 18px;
    color: var(--color-text-primary);
    letter-spacing: -0.01em;
  }

  p {
    margin-top: 8px;
    font-size: 14px;
    line-height: 1.6;
    color: var(--color-text-secondary);
  }
}

.startup-page__feature--wide {
  grid-column: span 3;
}

.startup-page__feature--accent {
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-bg-primary) 92%, transparent), var(--color-bg-primary)),
    linear-gradient(110deg, color-mix(in srgb, var(--color-accent) 10%, transparent), transparent);
}

.startup-page__footnote {
  margin-top: 14px;
  display: inline-flex;
  align-items: center;
  gap: 9px;
}

.startup-page__footnote-line {
  width: 42px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--gold-1), var(--gold-2), var(--gold-3));
}

.startup-page__footnote-text {
  font-size: 12px;
  color: var(--color-text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

@keyframes startup-gold-flow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@media (max-width: 960px) {
  .startup-page {
    width: calc(100vw - 28px);
    padding-top: 14px;
    gap: 12px;
  }

  .startup-page__hero {
    grid-template-columns: 1fr;
  }

  .startup-page__hero-side {
    border-left: 0;
    border-top: 1px solid color-mix(in srgb, var(--color-border-light) 78%, transparent);
    padding-left: 0;
    padding-top: 12px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .startup-page__feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .startup-page__feature,
  .startup-page__feature--wide {
    grid-column: span 1;
  }
}

@media (max-width: 640px) {
  .startup-page {
    width: calc(100vw - 18px);
    padding-top: 10px;
  }

  .startup-page__hero,
  .startup-page__panel {
    border-radius: 14px;
  }

  .startup-page__title {
    font-size: clamp(26px, 8.6vw, 38px);
    max-width: none;
  }

  .startup-page__subtitle {
    max-width: none;
    font-size: 14px;
    line-height: 1.62;
  }

  .startup-page__cta {
    display: grid;
    grid-template-columns: 1fr;
  }

  .startup-page__btn {
    width: 100%;
    justify-content: center;
  }

  .startup-page__hero-side {
    grid-template-columns: 1fr;
  }

  .startup-page__metric-value {
    font-size: 24px;
  }

  .startup-page__feature-grid {
    grid-template-columns: 1fr;
  }

  .startup-page__feature {
    padding: 14px;
  }

  .startup-page__feature h3 {
    font-size: 16px;
  }

  .startup-page__feature p {
    font-size: 13px;
  }
}

@media (max-height: 760px) {
  .startup-page {
    overflow: auto;
    padding-right: 6px;
  }
}
</style>
