<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Check, CheckCircle2, Copy, Info, UserRound } from 'lucide-vue-next'
import StepProgress from '@/components/StepProgress.vue'
import KnowledgeFileModal from '@/components/KnowledgeFileModal.vue'
import { getKnowledgeById } from '@/api'
import { useKnowledgeFlow } from '@/composables/useKnowledgeFlow'
import { pushToast } from '@/composables/useToast'
import type { KnowledgeFile } from '@/types'
import { formatKnowledgeTime } from '@/utils/knowledge'

const router = useRouter()
const { result, resetFlow } = useKnowledgeFlow()
const created = computed(() => result.value!.knowledge)
const completedAt = formatKnowledgeTime(result.value?.knowledge.created_at)
const fileOpen = ref(false)
const fileLoading = ref(false)
const file = ref<KnowledgeFile | null>(null)

const writeSteps = computed(() => result.value?.writes ?? [])

async function copyPath() {
  try {
    await navigator.clipboard.writeText(created.value.relative_path)
    pushToast('仓库路径已复制', 'success')
  } catch {
    pushToast('复制失败，请手动选择路径', 'error')
  }
}

async function continueInjection() {
  resetFlow()
  await router.replace({ name: 'knowledge-create' })
}

async function viewKnowledgeFile() {
  fileOpen.value = true
  fileLoading.value = true
  try {
    const response = await getKnowledgeById(created.value.id)
    file.value = response.knowledge
  } catch (reason) {
    fileOpen.value = false
    pushToast(reason instanceof Error ? reason.message : '无法读取知识文件', 'error')
  } finally {
    fileLoading.value = false
  }
}
</script>

<template>
  <div v-if="result" class="workflow-page completion-page">
    <div class="workflow-heading">
      <div>
        <h1>完成注入</h1>
        <p>知识已安全写入仓库，目录索引和审计日志已同步更新</p>
      </div>
      <StepProgress :current="3" />
    </div>

    <section class="completion-hero">
      <span class="success-orbit"><Check :size="49" stroke-width="2.6" /></span>
      <h2>知识注入成功</h2>
      <p>{{ created.scope === 'personal' ? '个人知识' : '团队知识' }}已作为 draft 写入知识库</p>
      <time>{{ completedAt }}</time>
    </section>

    <div class="completion-grid">
      <section class="knowledge-record-card">
        <h2>知识条目</h2>
        <a href="#" @click.prevent="viewKnowledgeFile">{{ created.id }}</a>
        <h3>{{ created.title }}</h3>
        <div class="tag-row">
          <span class="knowledge-tag">{{ created.scope }}</span>
          <span class="knowledge-tag">{{ created.layer }}</span>
          <span class="knowledge-tag">{{ created.maturity }}</span>
          <span class="knowledge-tag">{{ created.type }}</span>
        </div>
        <dl>
          <div v-if="created.owner_id"><dt>所有者</dt><dd>{{ created.owner_id }}</dd></div>
          <div><dt>来源</dt><dd>{{ (created.source_references ?? []).join('；') }}</dd></div>
        </dl>
        <h4>仓库路径</h4>
        <div class="path-box">
          <code>{{ created.relative_path }}</code>
          <button type="button" aria-label="复制仓库路径" @click="copyPath"><Copy :size="18" /></button>
        </div>
      </section>

      <section class="write-result-card">
        <h2>写入结果</h2>
        <ol class="write-timeline">
          <li v-for="item in writeSteps" :key="item.key" class="complete" :title="item.detail">
            <span><CheckCircle2 :size="24" /></span>
            <strong>{{ item.label }}</strong>
            <em>完成</em>
          </li>
        </ol>
        <p class="operator-line"><UserRound :size="19" />操作人：{{ result.actor?.id ?? '未知' }} · 角色：{{ result.actor?.role ?? '未知' }}</p>
      </section>
    </div>

    <footer class="workflow-actions">
      <p><Info :size="18" />新知识成熟度为 draft，后续由真实引用和验证推动提升</p>
      <div>
        <button class="button button-secondary button-wide" type="button" @click="continueInjection">继续注入</button>
        <button class="button button-primary button-wide" type="button" @click="viewKnowledgeFile">查看知识文件</button>
      </div>
    </footer>

    <KnowledgeFileModal :open="fileOpen" :knowledge="file" :loading="fileLoading" @close="fileOpen = false" />
  </div>
</template>
