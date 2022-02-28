<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme } from 'naive-ui'
import { Notebook } from '@vicons/tabler'
import { MaterialsIcon, EnableReaderIcon, DisableReaderIcon } from '../components/icons'
import PageLayout from '../components/PageLayout.vue'
import ProjectStatus from '../components/ProjectStatus.vue'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'
import MaterialIndex from './materials/MaterialIndex.vue'

const store = useStore();
const router = useRouter();

const osThemeRef = useOsTheme();

function reader(enable: boolean = true) {
    store.commit("setReaderMode", enable);
}

const version = import.meta.env.PACKAGE_VERSION;

document.title = `Home - Aexpy`;
</script>

<script lang="ts">
export default {
    components: {
        Notebook,
        MaterialsIcon, EnableReaderIcon, DisableReaderIcon
    }
}
</script>

<template>
    <PageLayout>
        <template #header>
            <n-page-header subtitle="Aexpy" @back="() => router.back()">
                <template #avatar>
                    <n-avatar>
                        <n-icon>
                            <notebook />
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
                <template #extra>
                </template>
                <template #footer>Aexpy</template>
            </n-page-header>
        </template>
        <n-tabs type="segment" style="height: 100%;">
            <n-tab-pane name="info" tab="Information" style="height: calc(100% - 52px);">
                <n-layout-content
                    content-style="padding: 10px;"
                    style="height: 100%;"
                    :native-scrollbar="false"
                >
                </n-layout-content>
            </n-tab-pane>
            <n-tab-pane name="materials" tab="Materials" style="height: calc(100% - 52px);">
                <n-layout-content
                    content-style="padding: 10px;"
                    style="height: 100%;"
                    :native-scrollbar="false"
                >
                </n-layout-content>
            </n-tab-pane>
        </n-tabs>
    </PageLayout>
</template>

<style scoped>
a {
    text-decoration: none;
    color: inherit;
}
</style>