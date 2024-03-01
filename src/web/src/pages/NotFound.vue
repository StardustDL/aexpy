
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NFlex, NText, NA, NBreadcrumb, NIcon, NAvatar, useMessage } from 'naive-ui'
import { RootIcon } from '../components/icons'
import { useRoute, useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'
import BuildStatus from '../components/BuildStatus.vue'
import NotFound from '../components/NotFound.vue'
import { Info } from '../models'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const params = route.params as {
    path: string[]
};

document.title = `Not Found - AexPy`;
</script>

<template>
    <n-flex vertical>
        <n-page-header @back="() => router.back()" :subtitle="`Not Found: /${params.path.join('/')}`">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="RootIcon" />
                </n-avatar>
            </template>
            <template #title>
                <n-text type="info">AexPy</n-text>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                </n-breadcrumb>
            </template>
            <template #footer>
                <BuildStatus />
            </template>
        </n-page-header>

        <NotFound :path="`/${params.path.join('/')}`" home size="huge"/>
    </n-flex>
</template>