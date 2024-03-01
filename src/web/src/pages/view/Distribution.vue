<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { NPageHeader, NFlex, NButtonGroup, NBreadcrumb, NIcon, useLoadingBar, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { DistributionIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ProjectBreadcrumbItem from '../../components/breadcrumbs/ProjectBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import { publicVars } from '../../services/utils'
import DistributionSwitch from '../../components/switches/DistributionSwitch.vue'
import LogSwitchPanel from '../../components/switches/LogSwitchPanel.vue'
import DescriptionLink from '../../components/links/DescriptionLink.vue'
import ReleasePrevSuccLink from '../../components/links/ReleasePrevSuccLink.vue'

const store = useStore();
const router = useRouter();
const message = useMessage();
const loadingbar = useLoadingBar();

const props = defineProps<{
    project: string,
    version: string,
}>();
const release = computed(() => new Release(props.project, props.version));

const data = ref<Distribution>();
const error = ref<boolean>(false);

async function load() {
    data.value = undefined;
    error.value = false;

    loadingbar.start();
    try {
        data.value = await store.state.api.distribution(release.value);
        publicVars({ "data": data.value });
    }
    catch (e) {
        console.error(e);
        error.value = true;
        message.error(`Failed to load preprocessed data for ${release.value}.`);
    }

    if (error.value) {
        loadingbar.error();
    }
    else {
        loadingbar.finish();
    }
}

onMounted(async () => await load());
watch(release, () => load());
</script>

<template>
    <n-flex vertical>
        <n-page-header :title="release?.toString() ?? 'Unknown'" subtitle="Distribution" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="DistributionIcon" />
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ProjectBreadcrumbItem />
                    <ReleaseBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-flex v-if="data" :align="'center'">
                    <MetadataViewer :data="data" />
                    <n-button-group size="small" v-if="release">
                        <ReleasePrevSuccLink :release="release" kind="preprocessed" />
                        <DescriptionLink :release="release" />
                    </n-button-group>
                    <LogSwitchPanel :load="() => store.state.api.apiLog(release)" />
                </n-flex>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath" size="huge"></NotFound>
        <n-spin v-else-if="!data" :size="160" style="width: 100%; margin: 50px"></n-spin>

        <DistributionViewer :data="data" v-if="data" />
    </n-flex>
</template>
