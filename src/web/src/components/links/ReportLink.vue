<script setup lang="ts">
import { NButton, NIcon, NTooltip } from 'naive-ui'
import { ReportIcon } from '../icons'
import { reportUrl } from '../../services/utils'
import { ReleasePair } from '../../models';

defineProps<{
    pair: ReleasePair
}>();

</script>

<template>
    <router-link :to="reportUrl(pair)" custom v-slot="{ href, navigate }">
        <n-button tag="a" :href="href" @click="navigate" type="info" ghost>
            <n-tooltip>
                <template #trigger>
                    <n-icon size="large" :component="ReportIcon" />
                </template>
                {{ pair }}
            </n-tooltip>
        </n-button>
    </router-link>
</template>