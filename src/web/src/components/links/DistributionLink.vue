<script setup lang="ts">
import { NButton, NIcon, NTooltip } from 'naive-ui'
import { DistributionIcon } from '../icons'
import { distributionUrl } from '../../services/utils'
import { Release } from '../../models';

defineProps<{
    release: Release
}>();

</script>

<template>
    <router-link :to="distributionUrl(release)" custom v-slot="{ href, navigate }">
        <n-button tag="a" :href="href" @click="navigate" type="info" ghost>
            <n-tooltip>
                <template #trigger>
                    <n-icon size="large" :component="DistributionIcon" />
                </template>
                {{ release }}
            </n-tooltip>
        </n-button>
    </router-link>
</template>