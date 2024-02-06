<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NPageHeader, NSpace, NButtonGroup, NBreadcrumb, NIcon, useLoadingBar, NAvatar, NLog, NSwitch, NButton, useMessage, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, DistributionIcon, DescriptionIcon, ReleaseIcon, LogIcon, DiffIcon, ReportIcon, CountIcon, EvaluateIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DifferenceBreadcrumbItem from '../../components/breadcrumbs/DifferenceBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiDifference, ProduceMode, ReleasePair } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import ApiDifferenceViewer from '../../components/products/ApiDifferenceViewer.vue'
import { publicVars } from '../../services/utils'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = route.params as {
    id: string,
};

const showDists = ref<boolean>(false);
const showStats = ref<boolean>(true);

let mode: ProduceMode = parseInt(route.query.mode?.toString() ?? ProduceMode.Access.toString()) as ProduceMode;

const release = ref<ReleasePair>();
const data = ref<ApiDifference>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>();

onMounted(async () => {
    loadingbar.start();
    release.value = ReleasePair.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.change(release.value);
            publicVars({ "data": data.value });
            mode = ProduceMode.Access;
        }
        catch (e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load data for ${params.id}.`);
        }
    }
    else {
        error.value = true;
        message.error('Invalid release ID');
    }

    if (error.value) {
        loadingbar.error();
    }
    else {
        loadingbar.finish();
    }
});

async function onLog(value: boolean) {
    if (release.value && value) {
        if (logcontent.value == undefined) {
            try {
                logcontent.value = await store.state.api.changeLog(release.value);
                publicVars({ "log": logcontent.value });
            }
            catch {
                message.error(`Failed to load log for ${params.id}.`);
            }
        }
    }
}

</script>

<template>
    <n-space vertical>
        <n-page-header
            :title="release?.toString() ?? 'Unknown'"
            subtitle="API Difference"
            @back="() => router.back()"
        >
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
                    <DifferenceBreadcrumbItem />
                    <ReleasePairBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space v-if="data">
                    <MetadataViewer :data="data" />
                    <n-button-group size="small" v-if="release">
                        <n-button
                            tag="a"
                            :href="`/distributions/${release.old.toString()}/`"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <DistributionIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/apis/${release.old.toString()}/`"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <DescriptionIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/distributions/${release.new.toString()}/`"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <DistributionIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/apis/${release.new.toString()}/`"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <DescriptionIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/reports/${release.toString()}/`"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <ReportIcon />
                            </n-icon>
                        </n-button>
                    </n-button-group>
                    <n-switch v-model:value="showlog" @update-value="onLog">
                        <template #checked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>
                        </template>
                    </n-switch>
                    <n-switch v-model:value="showDists">
                        <template #checked>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>
                        </template>
                    </n-switch>
                    <n-switch v-model:value="showStats">
                        <template #checked>
                            <n-icon size="large">
                                <CountIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <CountIcon />
                            </n-icon>
                        </template>
                    </n-switch>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>
        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <ApiDifferenceViewer
            v-if="data"
            :data="data"
            :show-stats="showStats"
            :show-dists="showDists"
        />

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-spin v-if="logcontent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>