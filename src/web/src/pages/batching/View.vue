<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NDrawer, NDrawerContent, NBreadcrumbItem, NSwitch, NCollapse, NCollapseItem, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, BatchIcon, ReleaseIcon, LogIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription, ProjectResult } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import BatchBreadcrumbItem from '../../components/breadcrumbs/BatchBreadcrumbItem.vue'
import DistributionViewer from '../../components/metadata/DistributionViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const params = <{
    provider: string,
    id: string,
}>route.params;

const release = ref<string>("");
const data = ref<ProjectResult>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
    release.value = params.id;
    if (release.value) {
        try {
            data.value = await store.state.api.batcher.index(release.value, params.provider);
        }
        catch (e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load data for ${params.id} by provider ${params.provider}.`);
        }
    }
    else {
        error.value = true;
        message.error('Invalid release ID');
    }
});

async function onLog(value: boolean) {
    if (release.value && value) {
        if (logcontent.value == "") {
            try {
                logcontent.value = await store.state.api.batcher.log(release.value, params.provider);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}
</script>

<template>
    <n-space vertical>
        <n-page-header
            :title="release?.toString() ?? 'Unknown'"
            subtitle="Batching"
            @back="() => router.back()"
        >
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
                    <n-breadcrumb-item>
                        <n-space>
                            <n-icon>
                                <ReleaseIcon />
                            </n-icon>
                            {{ release?.toString() ?? "Unknown" }}
                        </n-space>
                    </n-breadcrumb-item>
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space v-if="data">
                    <MetadataViewer :data="data" />
                    <n-switch v-model:value="showlog" @update-value="onLog">
                        <template #checked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>Show Log
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>Hide Log
                        </template>
                    </n-switch>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-space vertical size="large">
            <n-descriptions title="Batching Result" v-if="data">
                <n-descriptions-item>
                    <template #label>Releases</template>
                    {{ data.releases.length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Preprocessed</template>
                    {{ data.preprocessed.length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Extracted</template>
                    {{ data.extracted.length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Diffed</template>
                    {{ data.diffed.length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Evaluated</template>
                    {{ data.evaluated.length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Reported</template>
                    {{ data.reported.length }}
                </n-descriptions-item>
            </n-descriptions>
            <n-collapse>
                <n-collapse-item title="青铜" name="1">
                    <div>可以</div>
                </n-collapse-item>
                <n-collapse-item title="白银" name="2">
                    <div>很好</div>
                </n-collapse-item>
                <n-collapse-item title="黄金" name="3">
                    <div>真棒</div>
                </n-collapse-item>
            </n-collapse>
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="50"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
