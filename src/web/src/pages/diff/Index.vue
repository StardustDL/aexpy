<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, DiffIcon, GoIcon, PipelineIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DiffBreadcrumbItem from '../../components/breadcrumbs/DiffBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Pipeline, Release, ReleasePair } from '../../models'
import ReleasePairSetter from '../../components/metadata/ReleasePairSetter.vue'
import PipelineSetter from '../../components/metadata/PipelineSetter.vue'
import GoButton from '../../components/metadata/GoButton.vue'

const store = useStore();
const router = useRouter();

const inputPipeline = ref<Pipeline>(new Pipeline());
const inputValue = ref<ReleasePair>(new ReleasePair(new Release("click", "0.3"), new Release("click", "0.4")));

const goUrl = computed(() => `/diff/${inputPipeline.value.toString()}/${inputValue.value.toString()}/`)

</script>

<template>
    <n-space vertical>
        <n-page-header title="Diff" subtitle="AexPy" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <DiffIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <DiffBreadcrumbItem />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space vertical>
                    <n-input-group>
                        <PipelineSetter :pipeline="inputPipeline" />
                        <ReleasePairSetter :pair="inputValue" />
                        <GoButton :url="goUrl" />
                    </n-input-group>
                </n-space>
            </template>
        </n-page-header>

        <iframe
            :src="`${store.state.api.baseUrl}/data/diff`"
            :style="{ 'border-width': '0px', 'width': '100%', 'height': '600px' }"
        ></iframe>
    </n-space>
</template>