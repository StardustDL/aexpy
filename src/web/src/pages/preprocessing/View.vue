<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NInput, NInputGroup, NDivider, NInputGroupLabel, NCollapseTransition, NCode, NText, NButtonGroup, NBreadcrumb, NIcon, NLayoutContent, useLoadingBar, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, LinkIcon, ReleaseIcon, GoIcon, ExtractIcon, LogIcon, PreprocessIcon, FileIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import PreprocessBreadcrumbItem from '../../components/breadcrumbs/PreprocessBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, ProducerOptions, Release } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = <{
    provider: string,
    id: string,
}>route.params;

const showDists = ref<boolean>(true);

const query = ProducerOptions.fromQuery(route.query);

const release = ref<Release>();
const data = ref<Distribution>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>();

const homePath = computed(() => {
    if (data.value == undefined) return "";
    return `${data.value.release.project}-${data.value.release.version}.dist-info/METADATA`;
});

onMounted(async () => {
    loadingbar.start();
    release.value = Release.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.preprocessor.process(release.value, params.provider, query);
            query.redo = false;

            path.value = homePath.value;
            onGo();
        }
        catch(e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load preprocessed data for ${params.id} by provider ${params.provider}.`);
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
                logcontent.value = await store.state.api.preprocessor.log(release.value, params.provider, query);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}

const path = ref("");
const filecontent = ref<string>();
const fileloading = ref(false);

async function onGo() {
    if (data.value == undefined) {
        return;
    }
    loadingbar.start();
    fileloading.value = true;
    try {
        filecontent.value = await store.state.api.raw.text(`${data.value.wheelDir}/${path.value}`);
        loadingbar.finish();
    }
    catch (e) {
        message.error(`Failed to load file ${path.value}`);
        filecontent.value = undefined;
        loadingbar.error();
    }
    fileloading.value = false;
}
</script>

<template>
    <n-space vertical>
        <n-page-header
            :title="release?.toString() ?? 'Unknown'"
            subtitle="Preprocessing"
            @back="() => router.back()"
        >
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <PreprocessIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <PreprocessBreadcrumbItem />
                    <ReleaseBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space v-if="data">
                    <MetadataViewer :data="data" />
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
                    <n-button-group size="small" v-if="release">
                        <n-button
                            tag="a"
                            :href="`/extracting/${params.provider}/${release.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <ExtractIcon />
                            </n-icon>
                        </n-button>
                    </n-button-group>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>
        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-space v-if="data" vertical>
            <n-collapse-transition :show="showDists">
                <n-divider>Distribution</n-divider>
                <DistributionViewer :data="data" />
            </n-collapse-transition>
            <n-divider>Files</n-divider>
            <n-input-group size="large">
                <n-input-group-label size="large">
                    <n-icon>
                        <FileIcon />
                    </n-icon>
                </n-input-group-label>

                <n-input
                    size="large"
                    v-model:value="path"
                    placeholder="Path"
                    clearable
                    :loading="fileloading"
                    @keyup.enter="onGo"
                ></n-input>
                <n-button size="large" @click="() => { path = homePath; onGo(); }">
                    <n-icon size="large">
                        <HomeIcon />
                    </n-icon>
                </n-button>
                <n-button
                    size="large"
                    ghost
                    tag="a"
                    :href="store.state.api.raw.getUrl(`${data.wheelDir}/${path}`)"
                    target="_blank"
                >
                    <n-icon size="large">
                        <LinkIcon />
                    </n-icon>
                </n-button>
                <n-button size="large" type="primary" @click="onGo" :style="{ width: '10%' }">
                    <n-icon size="large">
                        <GoIcon />
                    </n-icon>
                </n-button>
            </n-input-group>
            <n-code :code="filecontent" language="python" v-if="filecontent != undefined" word-wrap></n-code>
            <NotFound v-else :path="path" :home="false"></NotFound>
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-spin v-if="logcontent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
