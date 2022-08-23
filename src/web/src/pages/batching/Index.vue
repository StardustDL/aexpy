<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NInputGroupLabel, NIcon, NSwitch, NLayoutContent, NPopconfirm, NAvatar, NCheckbox, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, BatchIcon, GoIcon, PipelineIcon, BatchIndexIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import BatchBreadcrumbItem from '../../components/breadcrumbs/BatchBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ProduceMode, Pipeline } from '../../models'
import PipelineSetter from '../../components/metadata/PipelineSetter.vue'
import GoButton from '../../components/metadata/GoButton.vue'

const store = useStore();
const router = useRouter();

const inputPipeline = ref<Pipeline>(new Pipeline());
const inputValue = ref<string>("coxbuild");

const goUrl = computed(() => `/batching/${inputPipeline.value.toString()}/${inputValue.value.toString()}/`)

</script>

<template>
    <n-space vertical>
        <n-page-header title="Batching" subtitle="AexPy" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <BatchIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <BatchBreadcrumbItem />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space vertical>
                    <n-input-group size="large">
                        <PipelineSetter :pipeline="inputPipeline" />
                        <n-input-group-label size="large">
                            <n-icon>
                                <ReleaseIcon />
                            </n-icon>
                        </n-input-group-label>
                        <n-input v-model:value="inputValue" placeholder="Release" size="large">
                        </n-input>
                        <GoButton :url="goUrl" :query="{ index: true }">
                            <BatchIndexIcon />
                        </GoButton>
                        <GoButton :url="goUrl" type="warning"/>
                    </n-input-group>
                </n-space>
            </template>
        </n-page-header>

        <iframe :src="`${store.state.api.baseUrl}/data/batch`"
            :style="{ 'border-width': '0px', 'width': '100%', 'height': '600px' }"></iframe>
    </n-space>
</template>