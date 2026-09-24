<template>
  <div class="student-app">
    <router-view />
    <!-- 底部导航（非功能子页面显示） -->
    <div v-if="showTabBar" class="tab-bar">
      <div v-for="tab in tabs" :key="tab.path"
        class="tab-item" :class="{ active: isActive(tab.path) }"
        @click="$router.push(tab.path)">
        <el-icon :size="22"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { path: '/subjects', label: '学科', icon: 'Reading' },
  { path: '/mistakes', label: '错题集', icon: 'Collection' },
  { path: '/profile',  label: '我的',  icon: 'User' },
]

// 只在一级页面显示底部导航
const tabBarPaths = ['/subjects', '/mistakes', '/profile']
const showTabBar = computed(() => tabBarPaths.includes(route.path))

const isActive = (path) => route.path === path || route.path.startsWith(path + '/')
</script>

<style scoped>
.student-app {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #F8F9FB;
  position: relative;
}
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  background: white;
  border-top: 1px solid #E5E7EB;
  display: flex;
  z-index: 100;
}
.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0 14px;
  cursor: pointer;
  color: #9CA3AF;
  font-size: 11px;
  gap: 3px;
  transition: color 0.2s;
}
.tab-item.active { color: #4A7CFF; }
</style>
