<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, ReportIcon, GoIcon, PipelineIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReportBreadcrumbItem from '../../components/breadcrumbs/ReportBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Pipeline, Release, ReleasePair } from '../../models'
import ReleasePairSetter from '../../components/metadata/ReleasePairSetter.vue'
import PipelineSetter from '../../components/metadata/PipelineSetter.vue'

const store = useStore();
const router = useRouter();

const inputPipeline = ref<Pipeline>(new Pipeline());
const inputValue = ref<ReleasePair>(new ReleasePair(new Release("click", "0.3"), new Release("click", "0.4")));

function onGo() {
    router.push({
        path: `/reporting/${inputPipeline.value}/${inputValue.value.toString()}/`,
        query: <any>inputOptions.value,
    });
}

</script>

<template>
    <n-space vertical>
        <n-page-header title="Reporting" subtitle="AexPy" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <ReportIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ReportBreadcrumbItem />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space vertical>
                    <n-input-group>
                        <PipelineSetter :pipeline="inputPipeline" />
                        <ReleasePairSetter :pair="inputValue" />
                        <n-button
                            type="primary"
                            @click="onGo"
                            :style="{ width: '10%' }"
                            size="large"
                        >
                            <n-icon size="large">
                                <GoIcon />
                            </n-icon>
                        </n-button>
                    </n-input-group>
                </n-space>
            </template>
        </n-page-header>

        <iframe
            :src="`${store.state.api.baseUrl}/data/reporting`"
            :style="{ 'border-width': '0px', 'width': '100%', 'height': '600px' }"
        ></iframe>
    </n-space>
</template>