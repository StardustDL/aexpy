<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NSelect, SelectOption, NInputGroupLabel, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, GoIcon, PipelineIcon, ReleaseIcon } from '../icons'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from '../../services/store'
import { Pipeline, Release } from '../../models'

const store = useStore();
const router = useRouter();
const route = useRoute();

const pipelines = ref<string[]>([]);
const loading = ref<boolean>(false);
const options = computed(() => {
    return pipelines.value.map(r => {
        return {
            label: r,
            value: r,
        }
    });
});
const pipeline = ref("");
const originalPipeline = computed(() => {
    for (let pro of pipelines.value) {
        if (route.fullPath.includes(`/${pro}/`)) {
            return pro;
        }
    }
    return "";
});

onMounted(async () => {
    try {
        pipelines.value = await store.state.api.generator.pipelines();
    }
    catch {
    }

    pipeline.value = originalPipeline.value;
});


</script>

<template>
    <n-input-group>
        <n-input-group-label size="small">
            <n-icon>
                <ProviderIcon />
            </n-icon>
        </n-input-group-label>
        <n-select
            v-model:value="pipeline"
            filterable
            placeholder="Provider"
            :options="options"
            :loading="loading"
            clearable
            size="small"
        />
        <n-button
            size="small"
            tag="a"
            :href="route.fullPath.replace(`/${originalPipeline}/`, `/${pipeline}/`)"
            target="_blank"
        >
            <template #icon>
                <n-icon>
                    <GoIcon />
                </n-icon>
            </template>
        </n-button>
    </n-input-group>
</template>