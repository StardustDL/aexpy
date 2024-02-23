<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'
import { DifferenceIcon } from '../icons'
import { changeUrl } from '../../services/utils'
import { ReleasePair } from '../../models';

defineProps<{
    pair: ReleasePair
}>();

</script>

<template>
    <router-link :to="changeUrl(pair)" custom v-slot="{ href, navigate }">
        <n-button tag="a" :href="href" @click="navigate" type="info" ghost>
            <n-icon size="large" :component="DifferenceIcon" />
        </n-button>
    </router-link>
</template>