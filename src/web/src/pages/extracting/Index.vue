<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, ExtractIcon, GoIcon, PipelineIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ExtractBreadcrumbItem from '../../components/breadcrumbs/ExtractBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ProduceMode, Pipeline, Release } from '../../models'
import ReleaseSetter from '../../components/metadata/ReleaseSetter.vue'
import PipelineSetter from '../../components/metadata/PipelineSetter.vue'
import GoButton from '../../components/metadata/GoButton.vue'

const store = useStore();
const router = useRouter();

const inputPipeline = ref<Pipeline>(new Pipeline());
const inputValue = ref<Release>(new Release("coxbuild", "0.1.0"));

const goUrl = computed(() => `/extracting/${inputPipeline.value.toString()}/${inputValue.value.toString()}/`)

</script>

<template>
    <n-space vertical>
        <n-page-header title="Extracting" subtitle="AexPy" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <ExtractIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ExtractBreadcrumbItem />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space vertical>
                    <n-input-group>
                        <PipelineSetter :pipeline="inputPipeline" />
                        <ReleaseSetter :release="inputValue" />
                        <GoButton :url="goUrl" />
                    </n-input-group>
                </n-space>
            </template>
        </n-page-header>

        <iframe
            :src="`${store.state.api.baseUrl}/data/extract`"
            :style="{ 'border-width': '0px', 'width': '100%', 'height': '600px' }"
        ></iframe>
    </n-space>
</template>