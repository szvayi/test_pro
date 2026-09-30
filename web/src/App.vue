<script setup>
import { onMounted, ref } from 'vue'

const health = ref(null)
const readiness = ref(null)
const routes = ref([])
const loading = ref(true)
const error = ref('')

async function loadApiData() {
  loading.value = true
  error.value = ''

  try {
    const [healthResponse, routesResponse, readinessResponse] = await Promise.all([
      fetch('/api/health'),
      fetch('/api/routes'),
      fetch('/readyz'),
    ])

    if (!healthResponse.ok || !routesResponse.ok) {
      throw new Error('API 请求失败')
    }

    health.value = await healthResponse.json()
    routes.value = (await routesResponse.json()).items

    if (readinessResponse.ok) {
      readiness.value = await readinessResponse.json()
    } else {
      const readinessError = await readinessResponse.json().catch(() => ({}))
      readiness.value = {
        status: 'not_ready',
        message: readinessError.detail || '数据库尚未就绪',
      }
    }
  } catch (requestError) {
    error.value = requestError.message || '无法连接到 API 服务'
  } finally {
    loading.value = false
  }
}

onMounted(loadApiData)
</script>

<template>
  <main class="page-shell">
    <section class="hero-card">
      <div class="hero-copy">
        <span class="eyebrow">FASTAPI × VUE 3</span>
        <h1>欢迎来到 Test Pro</h1>
        <p>一个简洁的全栈示例，前端正在调用后端接口。</p>
        <button class="refresh-button" type="button" @click="loadApiData">
          {{ loading ? '加载中…' : '重新检查接口' }}
        </button>
      </div>
      <div class="hero-mark" aria-hidden="true">✦</div>
    </section>

    <p v-if="error" class="error-message">{{ error }}</p>

    <section class="status-grid">
      <article class="info-card status-card">
        <div class="card-heading">
          <span>服务状态</span>
          <span class="status-dot" :class="{ online: health?.status === 'ok' }"></span>
        </div>
        <strong>{{ health?.status === 'ok' ? '运行正常' : '等待连接' }}</strong>
        <p>{{ health?.message || '正在请求健康检查接口…' }}</p>
      </article>

      <article class="info-card">
        <div class="card-heading">
          <span>已接入接口</span>
          <span class="count-badge">{{ routes.length }}</span>
        </div>
        <strong>API 清单</strong>
        <p>接口信息由后端动态返回。</p>
      </article>

      <article class="info-card readiness-card">
        <div class="card-heading">
          <span>数据库状态</span>
          <span class="status-dot" :class="{ online: readiness?.status === 'ok' }"></span>
        </div>
        <strong>{{ readiness?.status === 'ok' ? '已就绪' : '未就绪' }}</strong>
        <p>{{ readiness?.message || '正在检查数据库连接…' }}</p>
      </article>
    </section>

    <section class="routes-panel">
      <div class="panel-heading">
        <div>
          <span class="eyebrow">AVAILABLE ENDPOINTS</span>
          <h2>API 接口列表</h2>
        </div>
        <span class="panel-tip">实时数据</span>
      </div>

      <div v-if="routes.length" class="route-list">
        <article v-for="route in routes" :key="route.path" class="route-item">
          <span class="method">{{ route.method }}</span>
          <div class="route-content">
            <code>{{ route.path }}</code>
            <span>{{ route.name }} · {{ route.description }}</span>
          </div>
        </article>
      </div>
      <p v-else class="empty-state">暂无接口数据</p>
    </section>
  </main>
</template>
