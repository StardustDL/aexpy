<script setup lang="ts">
import { NIcon, NFlex, NTime, NStatistic, useMessage } from 'naive-ui'
import { BrandGithub, At, License, GitCommit, Clock, Notes, Help, Sitemap, Package, BrandDocker } from '@vicons/tabler'
import { Info } from '../models';
import { useStore } from '../services/store'
import { onMounted, ref } from 'vue';

const store = useStore();
const message = useMessage();

const info = ref<Info>();

onMounted(async () => {
    try {
        info.value = await store.state.api.info();
    }
    catch (e) {
        console.error(e);
        message.error(`Failed to load AexPy information.`);
    }
});
</script>

<template>
    <n-flex size="large">
        <n-statistic label="Author">
            <template #prefix>
                <n-icon :component="At" />
            </template>
            <a href="https://stardustdl.github.io/" style="text-decoration: none; color: inherit;">StardustDL</a>
        </n-statistic>
        <n-statistic label="Paper">
            <template #prefix>
                <n-icon :component="Notes" />
            </template>
            <a href="https://doi.org/10.1109/ISSRE55969.2022.00052" style="text-decoration: none; color: inherit;">ISSRE</a>
        </n-statistic>
        <n-statistic label="Source">
            <template #prefix>
                <n-icon :component="BrandGithub" />
            </template>
            <a href="https://github.com/StardustDL/aexpy" style="text-decoration: none; color: inherit;">GitHub</a>
        </n-statistic>
        <n-statistic label="License">
            <template #prefix>
                <n-icon :component="License" />
            </template>
            <a href="https://github.com/StardustDL/aexpy/blob/main/LICENSE"
                style="text-decoration: none; color: inherit;">MPL-2.0</a>
        </n-statistic>
        <n-statistic label="Document">
            <template #prefix>
                <n-icon :component="Help" />
            </template>
            <a href="https://aexpy-docs.netlify.app/" style="text-decoration: none; color: inherit;">Pages</a>
        </n-statistic>
        <n-statistic label="Index">
            <template #prefix>
                <n-icon :component="Sitemap" />
            </template>
            <a href="https://github.com/StardustDL-Labs/aexpy-index" style="text-decoration: none; color: inherit;">Data</a>
        </n-statistic>
        <n-statistic label="Package">
            <template #prefix>
                <n-icon :component="Package" />
            </template>
            <a href="https://pypi.org/project/aexpy/" style="text-decoration: none; color: inherit;">PyPI</a>
        </n-statistic>
        <n-statistic label="Image">
            <template #prefix>
                <n-icon :component="BrandDocker" />
            </template>
            <a href="https://hub.docker.com/r/stardustdl/aexpy" style="text-decoration: none; color: inherit;">Docker</a>
        </n-statistic>
        <n-statistic label="Commit" v-if="info">
            <template #prefix>
                <n-icon :component="GitCommit" />
            </template>
            <a :href="`https://github.com/StardustDL/aexpy/commit/${info.commitId}`"
                style="text-decoration: none; color: inherit;">{{ info.commitId.substring(0, 7) }}</a>
        </n-statistic>
        <n-statistic label="Build Date" v-if="info">
            <template #prefix>
                <n-icon :component="Clock" />
            </template>
            <n-time :time="info.buildDate" type="relative"></n-time>
        </n-statistic>
    </n-flex>
</template>