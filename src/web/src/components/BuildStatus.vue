<script setup lang="ts">
import { NIcon, NFlex, NTime, NStatistic } from 'naive-ui'
import { BrandGithub, At, License, GitCommit, Clock } from '@vicons/tabler'
import { Info } from '../models';

defineProps<{
    info: Info,
}>();
</script>

<template>
    <n-flex size="large">
        <n-statistic label="Author">
            <template #prefix>
                <n-icon :component="At" />
            </template>
            <a href="https://stardustdl.github.io/" style="text-decoration: none; color: inherit;">StardustDL</a>
        </n-statistic>
        <n-statistic label="License">
            <template #prefix>
                <n-icon :component="License" />
            </template>
            <a href="https://github.com/StardustDL/aexpy/blob/main/LICENSE"
                style="text-decoration: none; color: inherit;">MPL-2.0</a>
        </n-statistic>
        <n-statistic label="Source Code">
            <template #prefix>
                <n-icon :component="BrandGithub" />
            </template>
            <a href="https://github.com/StardustDL/aexpy" style="text-decoration: none; color: inherit;">GitHub</a>
        </n-statistic>
        <n-statistic label="Commit">
            <template #prefix>
                <n-icon :component="GitCommit" />
            </template>
            <a :href="`https://github.com/StardustDL/aexpy/commit/${info.commitId}`"
                style="text-decoration: none; color: inherit;">{{ info.commitId.substring(0, 7) }}</a>
        </n-statistic>
        <n-statistic label="Build Date">
            <template #prefix>
                <n-icon :component="Clock" />
            </template>
            <n-time :time="info.buildDate" type="relative"></n-time>
        </n-statistic>
    </n-flex>
</template>