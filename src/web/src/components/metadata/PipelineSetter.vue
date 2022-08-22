<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NSelect, SelectOption, NInputGroupLabel, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, GoIcon, PipelineIcon, ReleaseIcon } from '../icons'
import { useRouter } from 'vue-router'
import { useStore } from '../../services/store'
import { Pipeline, Release } from '../../models'
const props = defineProps<{
    pipeline: Pipeline,
}>();

const store = useStore();
const router = useRouter();

const loading = ref<boolean>(false);
const needRefresh = ref<boolean>(true);
const options = ref<SelectOption[]>([]);

async function onFocus() {
    if (!needRefresh.value)
        return;
    loading.value = true;
    try {
        let rels = await store.state.api.generator.pipelines();
        options.value = rels.map(r => {
            return {
                label: r,
                value: r,
            }
        });
    }
    catch {
        options.value = [];
    }
    needRefresh.value = false;
    loading.value = false;
}

</script>

<template>
    <n-input-group-label size="large">
        <n-icon>
            <PipelineIcon />
        </n-icon>
    </n-input-group-label>
    <n-select
        v-model:value="pipeline.name"
        filterable
        placeholder="Pipeline"
        :options="options"
        :loading="loading"
        @focus="onFocus"
        clearable
        size="large"
    />
</template>