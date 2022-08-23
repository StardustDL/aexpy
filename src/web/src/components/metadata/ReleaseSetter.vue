<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NSelect, SelectOption, NInputGroupLabel, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, VersionIcon, PreprocessIcon, GoIcon, PipelineIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import { useStore } from '../../services/store'
import { Release } from '../../models'

const props = defineProps<{
    release: Release,
}>();

const store = useStore();
const router = useRouter();

const loading = ref<boolean>(false);
const needRefresh = ref<boolean>(true);
const options = ref<SelectOption[]>([]);

async function onProjectChange(value: string) {
    needRefresh.value = true;
}

async function onFocus() {
    if (!needRefresh.value)
        return;
    loading.value = true;
    try {
        let rels = await store.state.api.generator.releases(props.release.project);
        options.value = rels.map(r => {
            return {
                label: r.version,
                value: r.version
            }
        });
        if (options.value.length >= 1) {
            props.release.version = options.value[options.value.length - 1].value?.toString() ?? "";
        }
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
            <ReleaseIcon />
        </n-icon>
    </n-input-group-label>
    <n-input v-model:value="release.project" placeholder="Project" @input="onProjectChange" size="large"></n-input>
    <n-input-group-label size="large">
        <n-icon>
            <VersionIcon />
        </n-icon>
    </n-input-group-label>
    <n-select v-model:value="release.version" filterable placeholder="Version" :options="options" :loading="loading" tag
        @focus="onFocus" clearable size="large" />
</template>