<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  ArrowUpRight,
  BookOpenCheck,
  BriefcaseBusiness,
  CalendarClock,
  Code2,
  FolderKanban,
  Layers3,
  RefreshCw,
  Search,
  ScrollText,
  UserRound,
} from 'lucide-vue-next'
import KnowledgeFileModal from '@/components/KnowledgeFileModal.vue'
import { getKnowledgeById, listKnowledge } from '@/api'
import { pushToast } from '@/composables/useToast'
import type {
  KnowledgeFile,
  KnowledgeLayer,
  KnowledgeListItem,
} from '@/types'
import { formatKnowledgeTime, formatReviewStatus } from '@/utils/knowledge'

type LayerChoice = {
  value?: KnowledgeLayer
  label: string
  description: string
  icon: typeof Layers3
  tone: string
}

const layerChoices: LayerChoice[] = [
  { label: '全部知识', description: '跨层查看', icon: Layers3, tone: 'all' },
  { value: 'layer0p', label: 'Layer 0-P', description: '个人经验', icon: UserRound, tone: 'personal' },
  { value: 'layer0t', label: 'Layer 0-T', description: '团队约定', icon: ScrollText, tone: 'convention' },
  { value: 'layer1', label: 'Layer 1', description: '技术知识', icon: Code2, tone: 'technical' },
  { value: 'layer2', label: 'Layer 2', description: '业务知识', icon: BriefcaseBusiness, tone: 'business' },
  { value: 'layer3', label: 'Layer 3', description: '项目知识', icon: FolderKanban, tone: 'project' },
]

const selectedLayer = ref<KnowledgeLayer | undefined>()
const items = ref<KnowledgeListItem[]>([])
const counts = ref<Record<KnowledgeLayer, number>>({
  layer0p: 0,
  layer0t: 0,
  layer1: 0,
  layer2: 0,
  layer3: 0,
})
const searchQuery = ref('')
const loading = ref(true)
const loadError = ref('')
const selectedKnowledge = ref<KnowledgeFile | null>(null)
const detailOpen = ref(false)
const detailLoading = ref(false)
let requestSequence = 0

const totalCount = computed(() => Object.values(counts.value).reduce((sum, count) => sum + count, 0))
const activeChoice = computed(() =>
  layerChoices.find((choice) => choice.value === selectedLayer.value) ?? layerChoices[0],
)
const visibleItems = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase('zh-CN')
  if (!query) return items.value
  return items.value.filter((item) => [
    item.id,
    item.title,
    item.type,
    item.owner_id ?? '',
    item.excerpt,
    ...item.tags,
  ].join(' ').toLocaleLowerCase('zh-CN').includes(query))
})

onMounted(loadKnowledge)
watch(selectedLayer, loadKnowledge)

function layerCount(layer?: KnowledgeLayer) {
  return layer ? counts.value[layer] : totalCount.value
}

function maturityLabel(maturity: KnowledgeListItem['maturity']) {
  return {
    draft: 'Draft',
    verified: 'Verified',
    proven: 'Proven',
  }[maturity]
}

async function loadKnowledge() {
  const currentRequest = ++requestSequence
  loading.value = true
  loadError.value = ''
  try {
    const response = await listKnowledge(selectedLayer.value)
    if (currentRequest !== requestSequence) return
    items.value = response.items
    counts.value = response.counts
  } catch (reason) {
    if (currentRequest !== requestSequence) return
    items.value = []
    loadError.value = reason instanceof Error ? reason.message : '知识列表加载失败'
  } finally {
    if (currentRequest === requestSequence) loading.value = false
  }
}

async function openKnowledge(item: KnowledgeListItem) {
  detailOpen.value = true
  detailLoading.value = true
  selectedKnowledge.value = null
  try {
    selectedKnowledge.value = (await getKnowledgeById(item.id)).knowledge
  } catch (reason) {
    detailOpen.value = false
    pushToast(reason instanceof Error ? reason.message : '知识文件读取失败', 'error')
  } finally {
    detailLoading.value = false
  }
}
</script>

<template>
  <div class="browse-page">
    <div class="browse-heading">
      <div>
        <span class="browse-eyebrow"><BookOpenCheck :size="16" />知识资产中心</span>
        <h1>知识浏览</h1>
        <p>按知识层级查看团队沉淀，快速定位需要的经验、规范与项目决策</p>
      </div>
      <div class="browse-total">
        <span>当前有效知识</span>
        <strong>{{ loading && !totalCount ? '—' : totalCount }}</strong>
        <small>条</small>
      </div>
    </div>

    <section class="layer-browser" aria-label="知识层级筛选">
      <div class="layer-tabs">
        <button
          v-for="choice in layerChoices"
          :key="choice.label"
          type="button"
          class="layer-tab"
          :class="[`layer-${choice.tone}`, { active: selectedLayer === choice.value }]"
          :aria-pressed="selectedLayer === choice.value"
          @click="selectedLayer = choice.value"
        >
          <span class="layer-tab-icon"><component :is="choice.icon" :size="21" /></span>
          <span class="layer-tab-copy">
            <strong>{{ choice.label }}</strong>
            <small>{{ choice.description }}</small>
          </span>
          <b>{{ layerCount(choice.value) }}</b>
        </button>
      </div>

      <div class="browse-toolbar">
        <div>
          <h2>{{ activeChoice.label }}</h2>
          <p>共 {{ layerCount(selectedLayer) }} 条，当前显示 {{ visibleItems.length }} 条</p>
        </div>
        <div class="browse-toolbar-actions">
          <label class="browse-search">
            <Search :size="18" />
            <input v-model="searchQuery" type="search" placeholder="搜索标题、ID、标签或正文" />
          </label>
          <button class="refresh-button" type="button" :disabled="loading" aria-label="刷新知识列表" @click="loadKnowledge">
            <RefreshCw :size="19" :class="{ spinning: loading }" />
          </button>
        </div>
      </div>

      <div v-if="loadError" class="browse-error" role="alert">
        <strong>暂时无法读取知识</strong>
        <span>{{ loadError }}</span>
        <button class="text-button" type="button" @click="loadKnowledge">重新加载</button>
      </div>

      <div v-else-if="loading" class="knowledge-card-grid" aria-label="正在加载知识">
        <div v-for="index in 6" :key="index" class="knowledge-card-skeleton">
          <i /><i /><i /><i />
        </div>
      </div>

      <div v-else-if="!visibleItems.length" class="browse-empty">
        <span><BookOpenCheck :size="30" /></span>
        <h3>{{ searchQuery ? '没有匹配的知识' : '当前 Layer 暂无知识' }}</h3>
        <p>{{ searchQuery ? '请尝试更换关键词或清空搜索条件。' : '完成知识注入后，新内容会自动出现在这里。' }}</p>
        <button v-if="searchQuery" class="button button-secondary" type="button" @click="searchQuery = ''">清空搜索</button>
      </div>

      <div v-else class="knowledge-card-grid">
        <button
          v-for="item in visibleItems"
          :key="item.id"
          type="button"
          class="browse-knowledge-card"
          @click="openKnowledge(item)"
        >
          <span class="knowledge-card-topline">
            <span class="card-layer-badge" :class="`badge-${item.layer}`">{{ item.layer === 'layer0p' ? 'Layer 0-P' : item.layer === 'layer0t' ? 'Layer 0-T' : item.layer.replace('layer', 'Layer ') }}</span>
            <span class="maturity-pill" :class="`maturity-${item.maturity}`"><i />{{ maturityLabel(item.maturity) }}</span>
          </span>
          <span class="knowledge-card-title-row">
            <strong>{{ item.title }}</strong>
            <ArrowUpRight :size="19" />
          </span>
          <span v-if="item.tags.length" class="knowledge-card-tags">
            <em v-for="tag in item.tags" :key="tag">#{{ tag }}</em>
          </span>
          <span class="knowledge-card-review" :class="{ overdue: item.review.overdue }">
            <span><CalendarClock :size="15" /><strong>Next Review</strong></span>
            <time :datetime="item.review.next_review_at">{{ formatKnowledgeTime(item.review.next_review_at) }}</time>
            <em v-if="item.review.overdue">{{ formatReviewStatus(item.review.overdue) }}</em>
          </span>
          <span class="knowledge-card-footer">
            <code>{{ item.id }}</code>
            <span>{{ item.scope === 'personal' ? `个人 · ${item.owner_id}` : '团队共享' }}</span>
            <time :datetime="item.created_at">{{ formatKnowledgeTime(item.created_at) }}</time>
          </span>
        </button>
      </div>
    </section>

    <KnowledgeFileModal
      :open="detailOpen"
      :knowledge="selectedKnowledge"
      :loading="detailLoading"
      @close="detailOpen = false"
    />
  </div>
</template>
