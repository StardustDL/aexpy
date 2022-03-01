<script setup lang="ts">
import { NIcon, NTime, NSpace, NTooltip, NTag, NAvatar } from 'naive-ui'
import { FaceId, FaceIdError } from '@vicons/tabler'

const props = defineProps<{
    success: boolean,
}>();

</script>

<template>
    <n-tag :type="props.success ? 'success' : 'error'">
        <n-space size="small">
            <n-icon size="large">
                <FaceId v-if="props.success"/>
                <FaceIdError v-else/>
            </n-icon>
            <span v-if="props.success">Success</span>
            <span v-else>Error</span>
        </n-space>
    </n-tag>
</template>