<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'
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
            <n-icon size="large" :component="DistributionIcon" />
        </n-button>
    </router-link>
</template>