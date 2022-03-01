<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage } from 'naive-ui'
import { HomeIcon, RootIcon } from '../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'

const store = useStore();
const router = useRouter();
const version = import.meta.env.PACKAGE_VERSION;
const message = useMessage();
</script>

<template>
    <n-page-header subtitle="Aexpy" @back="() => router.back()">
        <template #avatar>
            <n-avatar>
                <n-icon>
                    <RootIcon />
                </n-icon>
            </n-avatar>
        </template>
        <template #title>
            <n-text type="info">Aexpy</n-text>
        </template>
        <template #header>
            <n-breadcrumb>
                <HomeBreadcrumbItem />
            </n-breadcrumb>
        </template>
        <template #extra></template>
    </n-page-header>
</template>
