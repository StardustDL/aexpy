<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, CodeIcon, GoIcon, PipelineIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import CodeBreadcrumbItem from '../../components/breadcrumbs/CodeBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ProducerOptions, Pipeline, Release, ReleasePair } from '../../models'
import ReleasePairSetter from '../../components/metadata/ReleasePairSetter.vue'
import PipelineSetter from '../../components/metadata/PipelineSetter.vue'

const store = useStore();
const router = useRouter();

const editor = ref();

</script>

<template>
    <n-space vertical>
        <n-page-header title="Coding" subtitle="AexPy" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <CodeIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <CodeBreadcrumbItem />
                </n-breadcrumb>
            </template>
        </n-page-header>

        <n-text>Please use Console Window to run your code, api to access api server, data to access requested data, log to access running log.</n-text>
    </n-space>
</template>