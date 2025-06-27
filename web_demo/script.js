// 全局变量
let currentTaskId = null;
let currentFile = null;
let pollInterval = null;
let currentSettings = {};

// 录音相关变量
let mediaRecorder = null;
let audioStream = null;
let recordedChunks = [];
let recordingStartTime = null;
let recordingTimer = null;
let audioContext = null;
let analyser = null;
let visualizerAnimationId = null;

// DOM元素 - 将在DOMContentLoaded后初始化
let uploadArea, uploadBtn, fileInput, audioUrl, urlSubmitBtn, startBtn, resetBtn, recordBtn, statusSection, resultSection;
let enableItn, enablePunc, enableSpeaker, showUtterances, enableDialect, focusLastSpeakers;
let statusTitle, statusMessage, progressFill, taskId;
let resultText, audioDuration, utteranceCount, processTime, utterancesSection, utterancesList;
let downloadBtn, downloadJsonBtn, downloadWordBtn;

// 录音相关DOM元素
let recordingSection, recordingStatus, audioVisualizer, startRecordBtn, pauseRecordBtn, stopRecordBtn;
let recordingTime, recordingSize, recordingActions, playRecordingBtn, uploadRecordingBtn, discardRecordingBtn;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化DOM元素
    initializeDOMElements();
    // 初始化事件监听器
    initializeEventListeners();
    // 初始化其他功能
    initializeTaskHistory();
    initializeConfigItems();
    initializeTranscriptionCollapse();
    // 检查配置状态
    checkConfigurationStatus();
    // 更新UI状态
    updateUI('initial');
});

// 初始化DOM元素
function initializeDOMElements() {
    // 主要控件
    uploadArea = document.getElementById('uploadArea');
    uploadBtn = document.getElementById('uploadBtn');
    fileInput = document.getElementById('fileInput');
    audioUrl = document.getElementById('audioUrl');
    urlSubmitBtn = document.getElementById('urlSubmitBtn');
    startBtn = document.getElementById('startBtn');
    resetBtn = document.getElementById('resetBtn');
    recordBtn = document.getElementById('recordBtn');
    statusSection = document.getElementById('statusSection');
    resultSection = document.getElementById('resultSection');

    // 配置选项
    enableItn = document.getElementById('enableItn');
    enablePunc = document.getElementById('enablePunc');
    enableSpeaker = document.getElementById('enableSpeaker');
    showUtterances = document.getElementById('showUtterances');
    enableDialect = document.getElementById('enableDialect');
    focusLastSpeakers = document.getElementById('focusLastSpeakers');

    // 状态元素
    statusTitle = document.getElementById('statusTitle');
    statusMessage = document.getElementById('statusMessage');
    progressFill = document.getElementById('progressFill');
    taskId = document.getElementById('taskId');

    // 结果元素
    resultText = document.getElementById('resultText');
    audioDuration = document.getElementById('audioDuration');
    utteranceCount = document.getElementById('utteranceCount');
    processTime = document.getElementById('processTime');
    utterancesSection = document.getElementById('utterancesSection');
    utterancesList = document.getElementById('utterancesList');
    downloadBtn = document.getElementById('downloadBtn');
    downloadJsonBtn = document.getElementById('downloadJsonBtn');
    downloadWordBtn = document.getElementById('downloadWordBtn');

    // 录音相关元素
    recordingSection = document.getElementById('recordingSection');
    recordingStatus = document.getElementById('recordingStatus');
    audioVisualizer = document.getElementById('audioVisualizer');
    startRecordBtn = document.getElementById('startRecordBtn');
    pauseRecordBtn = document.getElementById('pauseRecordBtn');
    stopRecordBtn = document.getElementById('stopRecordBtn');
    recordingTime = document.getElementById('recordingTime');
    recordingSize = document.getElementById('recordingSize');
    recordingActions = document.getElementById('recordingActions');
    playRecordingBtn = document.getElementById('playRecordingBtn');
    uploadRecordingBtn = document.getElementById('uploadRecordingBtn');
    discardRecordingBtn = document.getElementById('discardRecordingBtn');
}

// 事件监听器
function initializeEventListeners() {
    // 文件上传
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // URL提交
    urlSubmitBtn.addEventListener('click', handleUrlSubmit);
    audioUrl.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleUrlSubmit();
        }
    });
    
    // 操作按钮
    startBtn.addEventListener('click', handleStartRecognition);
    if (recordBtn) recordBtn.addEventListener('click', handleRecordMode);
    resetBtn.addEventListener('click', handleReset);
    if (downloadBtn) downloadBtn.addEventListener('click', handleDownload);
    if (downloadJsonBtn) downloadJsonBtn.addEventListener('click', handleDownloadJson);
    if (downloadWordBtn) {
        downloadWordBtn.addEventListener('click', handleDownloadWord);
        // 初始状态设为禁用
        setWordDownloadButtonState(false);
    }

    // 录音按钮事件
    if (startRecordBtn) startRecordBtn.addEventListener('click', startRecording);
    if (pauseRecordBtn) pauseRecordBtn.addEventListener('click', pauseRecording);
    if (stopRecordBtn) stopRecordBtn.addEventListener('click', stopRecording);
    if (playRecordingBtn) playRecordingBtn.addEventListener('click', playRecording);
    if (uploadRecordingBtn) uploadRecordingBtn.addEventListener('click', uploadRecording);
    if (discardRecordingBtn) discardRecordingBtn.addEventListener('click', discardRecording);
}

// Word下载按钮状态管理
function setWordDownloadButtonState(enabled) {
    if (downloadWordBtn) {
        downloadWordBtn.disabled = !enabled;
        if (enabled) {
            downloadWordBtn.classList.remove('disabled');
            downloadWordBtn.style.opacity = '1';
            downloadWordBtn.style.cursor = 'pointer';
            downloadWordBtn.title = '下载Word格式的会议纪要';
        } else {
            downloadWordBtn.classList.add('disabled');
            downloadWordBtn.style.opacity = '0.5';
            downloadWordBtn.style.cursor = 'not-allowed';
            downloadWordBtn.title = '请等待会议纪要生成完成';
        }
    }
}

// 文件选择处理
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        currentFile = file;
        updateFileInfo(file);
        audioUrl.value = '';
    }
}

// 拖拽处理
function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (isValidAudioFile(file)) {
            currentFile = file;
            updateFileInfo(file);
            audioUrl.value = '';
        } else {
            showError('请选择有效的音频文件（MP3、WAV、OGG、RAW）');
        }
    }
}

// URL提交处理
function handleUrlSubmit() {
    const url = audioUrl.value.trim();
    if (url) {
        if (isValidUrl(url)) {
            currentFile = null;
            fileInput.value = '';
            updateUrlInfo(url);
        } else {
            showError('请输入有效的URL地址');
        }
    }
}

// 开始识别
function handleStartRecognition() {
    if (!currentFile && !audioUrl.value.trim()) {
        showError('请选择音频文件或输入URL');
        return;
    }

    updateUI('processing');

    // 检查是否有后端API
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        // 尝试使用真实API
        realRecognition();
    } else {
        // 使用模拟API
        simulateRecognition();
    }
}

// 重置
function handleReset() {
    currentFile = null;
    currentTaskId = null;
    window.currentAsyncTaskId = null; // 清除异步任务ID
    fileInput.value = '';
    audioUrl.value = '';

    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }

    // 禁用Word下载按钮
    setWordDownloadButtonState(false);

    updateUI('initial');
}

// 录音模式处理
function handleRecordMode() {
    showRecordingInterface();
}

// 下载结果
function handleDownload() {
    handleDownloadJson();
}

// 下载JSON结果
function handleDownloadJson() {
    const result = {
        taskId: currentTaskId,
        text: resultText.textContent,
        timestamp: new Date().toISOString(),
        config: {
            enableItn: enableItn.checked,
            enablePunc: enablePunc.checked,
            enableSpeaker: enableSpeaker.checked,
            showUtterances: showUtterances.checked
        }
    };

    const blob = new Blob([JSON.stringify(result, null, 2)], {
        type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `asr_result_${currentTaskId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 下载Word文档
async function handleDownloadWord() {
    // 检查按钮是否被禁用
    if (downloadWordBtn && downloadWordBtn.disabled) {
        showError('请等待会议纪要生成完成后再下载');
        return;
    }

    console.log('Word下载请求，当前异步任务ID:', window.currentAsyncTaskId);
    console.log('Word下载请求，当前原始任务ID:', currentTaskId);

    // 检查是否有异步任务ID
    if (!window.currentAsyncTaskId) {
        console.error('没有找到异步任务ID');
        showError('会议纪要尚未生成，请先生成会议纪要');
        return;
    }

    try {
        // 使用异步任务ID进行下载
        const downloadUrl = `/api/download_word/${window.currentAsyncTaskId}`;
        console.log('Word下载URL:', downloadUrl);

        const response = await fetch(downloadUrl);

        // 检查响应状态
        if (!response.ok) {
            // 如果响应不成功，尝试解析错误信息
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                throw new Error(errorData.error || '下载失败');
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        }

        // 检查响应类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/vnd.openxmlformats-officedocument.wordprocessingml.document')) {
            // 如果不是Word文档，可能是错误响应
            const text = await response.text();
            try {
                const errorData = JSON.parse(text);
                throw new Error(errorData.error || '返回的不是Word文档');
            } catch (parseError) {
                throw new Error('服务器返回了无效的响应');
            }
        }

        // 获取文件名
        const contentDisposition = response.headers.get('content-disposition');
        let filename = '会议纪要.docx';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }

        // 获取文件数据并下载
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('Word文档下载成功:', filename);

    } catch (error) {
        console.error('下载Word文档失败:', error);
        showError('Word文档下载失败: ' + error.message);
    }
}

// 模拟识别过程
function simulateRecognition() {
    // 生成模拟任务ID
    currentTaskId = generateTaskId();
    taskId.textContent = currentTaskId;
    
    let progress = 0;
    const startTime = Date.now();
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 95) progress = 95;
        
        progressFill.style.width = progress + '%';
        
        if (progress > 30 && progress < 60) {
            statusMessage.textContent = '正在进行语音识别...';
        } else if (progress >= 60) {
            statusMessage.textContent = '正在处理识别结果...';
        }
    }, 500);
    
    // 模拟完成
    setTimeout(() => {
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        const endTime = Date.now();
        const duration = Math.round((endTime - startTime) / 1000);
        
        // 模拟结果
        const mockResult = generateMockResult();
        displayResult(mockResult, duration);
        
        updateUI('completed');
    }, 3000 + Math.random() * 2000);
}

// 生成模拟结果
function generateMockResult() {
    const sampleTexts = [
        "欢迎使用火山引擎语音识别服务。我们提供高精度的语音转文字功能，支持多种音频格式和实时处理。",
        "人工智能技术正在快速发展，语音识别作为其中的重要分支，在智能助手、语音输入等场景中发挥着重要作用。",
        "今天的会议讨论了产品的发展方向，我们需要在用户体验和技术创新之间找到平衡点。",
        "语音识别技术的准确率不断提升，现在已经能够处理复杂的语音环境和多种方言。"
    ];
    
    const text = sampleTexts[Math.floor(Math.random() * sampleTexts.length)];
    const words = text.split('');
    const utterances = [];
    
    let currentTime = 0;
    let currentUtterance = '';
    
    for (let i = 0; i < words.length; i++) {
        currentUtterance += words[i];
        
        if (words[i] === '。' || words[i] === '，' || (i > 0 && i % 15 === 0)) {
            const startTime = currentTime;
            const duration = 1000 + Math.random() * 2000;
            currentTime += duration;
            
            utterances.push({
                text: currentUtterance.trim(),
                start_time: Math.round(startTime),
                end_time: Math.round(currentTime)
            });
            
            currentUtterance = '';
        }
    }
    
    if (currentUtterance.trim()) {
        utterances.push({
            text: currentUtterance.trim(),
            start_time: currentTime,
            end_time: currentTime + 1000
        });
    }
    
    return {
        text: text,
        utterances: utterances,
        audio_info: {
            duration: currentTime + 1000
        }
    };
}

// 显示结果
function displayResult(result, processTime) {
    const audioInfo = result.audio_info || {};
    const utterances = result.utterances || [];

    // 显示转录记录和会议纪要区域
    const transcriptionSection = document.getElementById('transcriptionSection');
    const meetingSummarySection = document.getElementById('meetingSummarySection');
    const statusSection = document.getElementById('statusSection');

    statusSection.style.display = 'none';
    transcriptionSection.style.display = 'block';
    meetingSummarySection.style.display = 'block';

    // 计算音频时长：如果audio_info中没有duration，从utterances中计算
    let duration = audioInfo.duration || 0;
    if (!duration && utterances.length > 0) {
        // 从最后一个utterance的end_time计算总时长（毫秒）
        const lastUtterance = utterances[utterances.length - 1];
        if (lastUtterance && lastUtterance.end_time) {
            duration = lastUtterance.end_time;
        }
    }

    // 更新音频信息（多个位置）
    const audioDurationElements = document.querySelectorAll('#audioDuration, #meetingDuration');
    const utteranceCountElements = document.querySelectorAll('#utteranceCount');
    const processTimeElements = document.querySelectorAll('#processTime');

    audioDurationElements.forEach(el => el.textContent = formatDuration(duration));
    utteranceCountElements.forEach(el => el.textContent = utterances.length);
    if (processTime) {
        processTimeElements.forEach(el => el.textContent = processTime + '秒');
    }

    // 显示转录内容
    displayUtterances(utterances);

    // 生成会议纪要（使用异步版本）
    if (currentTaskId) {
        generateMeetingMinutes(currentTaskId, result);
    }
}

// 显示分句详情
function displayUtterances(utterances) {
    const utterancesList = document.getElementById('utterancesList');
    utterancesList.innerHTML = '';

    utterances.forEach((utterance, index) => {
        const item = document.createElement('div');
        item.className = 'utterance-item';

        const timeSpan = document.createElement('span');
        timeSpan.className = 'utterance-time';
        timeSpan.textContent = `${index + 1}. ${formatDuration(utterance.start_time)}`;

        const textSpan = document.createElement('span');
        textSpan.className = 'utterance-text';
        textSpan.textContent = utterance.text;

        item.appendChild(timeSpan);
        item.appendChild(textSpan);
        utterancesList.appendChild(item);
    });
}

// 生成会议纪要（旧版本，用于兼容）
function generateMeetingMinutesOld(result, processTime) {
    // 如果有currentTaskId，调用新的异步版本
    if (currentTaskId) {
        generateMeetingMinutes(currentTaskId, result);
    } else {
        // 降级处理：使用本地生成
        generateLocalMeetingMinutes(result);
    }
}

// 更新UI状态
function updateUI(state) {
    const statusDiv = document.getElementById('status');
    const statusSection = document.getElementById('statusSection');
    const transcriptionSection = document.getElementById('transcriptionSection');
    const meetingSummarySection = document.getElementById('meetingSummarySection');
    const startBtn = document.getElementById('startBtn');
    const resetBtn = document.getElementById('resetBtn');

    switch (state) {
        case 'initial':
            statusSection.style.display = 'none';
            transcriptionSection.style.display = 'none';
            meetingSummarySection.style.display = 'none';
            statusDiv.style.display = 'none';  // 隐藏解决方案
            startBtn.style.display = 'inline-flex';
            resetBtn.style.display = 'none';
            break;

        case 'processing':
            statusSection.style.display = 'block';
            transcriptionSection.style.display = 'none';
            meetingSummarySection.style.display = 'none';
            startBtn.style.display = 'none';
            resetBtn.style.display = 'none';

            const statusTitle = document.getElementById('statusTitle');
            const statusMessage = document.getElementById('statusMessage');
            const progressFill = document.getElementById('progressFill');

            statusTitle.textContent = '处理中';
            statusMessage.textContent = '正在上传音频文件...';
            progressFill.style.width = '0%';
            break;

        case 'completed':
            statusSection.style.display = 'none';
            transcriptionSection.style.display = 'block';
            meetingSummarySection.style.display = 'block';
            startBtn.style.display = 'none';
            resetBtn.style.display = 'inline-flex';
            break;
    }
}

// 工具函数
function isValidAudioFile(file) {
    const validTypes = ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/x-wav', 'audio/aiff', 'audio/x-aiff', 'audio/mp4', 'audio/x-m4a'];
    const validExtensions = ['.mp3', '.wav', '.ogg', '.raw', '.aiff', '.m4a'];

    // 检查文件大小 (500MB)
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
        showError(`文件过大（${(file.size / (1024*1024)).toFixed(1)}MB），最大支持500MB`);
        return false;
    }

    const isValidType = validTypes.includes(file.type) ||
                       validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isValidType) {
        showError('不支持的文件格式。支持的格式：MP3、WAV、OGG、RAW、AIFF、M4A');
        return false;
    }

    return true;
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function updateFileInfo(file) {
    const uploadText = uploadArea.querySelector('.upload-text p');
    uploadText.textContent = `已选择文件: ${file.name} (${formatFileSize(file.size)})`;
}

function updateUrlInfo(url) {
    const uploadText = uploadArea.querySelector('.upload-text p');
    uploadText.textContent = `已设置URL: ${url}`;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(milliseconds) {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
        let result = hours + '小时';
        if (minutes > 0) result += minutes + '分';
        if (seconds > 0) result += seconds + '秒';
        return result;
    } else if (minutes > 0) {
        return minutes + '分' + (seconds > 0 ? seconds + '秒' : '');
    } else {
        return seconds + '秒';
    }
}

// 提取主要议题
function extractMainTopics(text, utterances) {
    const topics = [];

    // 基于关键词提取议题
    const keywordTopics = [
        { keywords: ['安全', '生产', '事故'], topic: '安全生产工作部署' },
        { keywords: ['财务', '预算', '成本', '营收'], topic: '财务状况分析与预算安排' },
        { keywords: ['人事', '招聘', '培训', '员工'], topic: '人力资源建设与管理' },
        { keywords: ['运营', '管理', '流程', '效率'], topic: '运营管理优化措施' },
        { keywords: ['市场', '客户', '产品', '销售'], topic: '市场拓展与产品发展' },
        { keywords: ['计划', '目标', '任务', '工作'], topic: '工作计划与目标制定' }
    ];

    keywordTopics.forEach(item => {
        if (item.keywords.some(keyword => text.includes(keyword))) {
            topics.push(item.topic);
        }
    });

    // 如果没有匹配到关键词，使用默认议题
    if (topics.length === 0) {
        topics.push('前期工作总结汇报');
        topics.push('当前重点任务分析');
        topics.push('下阶段工作部署');
    }

    return topics.slice(0, 5); // 最多5个议题
}

// 生成会议总结
function generateMeetingSummary(text, utterances) {
    const summaryPoints = [];

    if (text.includes('安全')) {
        summaryPoints.push('会议强调了安全生产的重要性，要求各部门严格落实安全责任制，确保不发生安全事故。');
    }

    if (text.includes('财务') || text.includes('预算')) {
        summaryPoints.push('财务工作取得积极进展，各项指标基本达到预期，下一步要继续加强成本控制和预算管理。');
    }

    if (text.includes('人事') || text.includes('员工')) {
        summaryPoints.push('人力资源建设需要进一步加强，要做好人才引进和员工培训工作，提升整体素质。');
    }

    if (utterances.length > 0) {
        const speakerCount = new Set(utterances.map(u => u.speaker_id || u.speaker)).size;
        summaryPoints.push(`本次会议共有${speakerCount}位同志发言，大家围绕会议主题进行了深入交流，达成了重要共识。`);
    }

    summaryPoints.push('与会人员一致认为，要进一步统一思想、明确目标，以更加务实的作风推动各项工作落实。');

    return summaryPoints;
}

// 生成行动项目
function generateActionItems(text, utterances) {
    const actionItems = [];

    if (text.includes('安全')) {
        actionItems.push('各部门要立即开展安全隐患排查，建立安全管理台账，确保安全措施落实到位');
    }

    if (text.includes('财务') || text.includes('预算')) {
        actionItems.push('财务部门要加强预算执行监控，定期分析财务状况，及时报告异常情况');
    }

    if (text.includes('人事') || text.includes('培训')) {
        actionItems.push('人事部门要制定详细的招聘和培训计划，确保人才队伍建设有序推进');
    }

    if (text.includes('计划') || text.includes('目标')) {
        actionItems.push('各部门要根据会议要求，制定具体的实施方案，明确时间节点和责任分工');
    }

    // 通用行动项目
    actionItems.push('会议纪要将及时分发给各参会单位，请认真组织学习贯彻');
    actionItems.push('各部门要建立工作台账，定期汇报工作进展情况');
    actionItems.push('下次会议将检查本次会议决议的落实情况');

    return actionItems;
}

// 本地生成会议纪要（降级处理）
function generateLocalMeetingMinutes(result) {
    // 隐藏欢迎页面
    const welcomeSection = document.getElementById('welcomeSection');
    if (welcomeSection) {
        welcomeSection.style.display = 'none';
    }

    // 显示会议纪要区域
    const meetingMinutesSection = document.getElementById('meetingMinutesSection');
    if (meetingMinutesSection) {
        meetingMinutesSection.style.display = 'block';
    }

    // 显示加载动画
    const minutesLoadingContainer = document.getElementById('minutesLoadingContainer');
    const minutesResult = document.getElementById('minutesResult');

    if (minutesLoadingContainer) {
        minutesLoadingContainer.style.display = 'flex';
    }
    if (minutesResult) {
        minutesResult.style.display = 'none';
    }

    // 开始步骤动画
    startLoadingSteps();

    // 模拟处理时间
    setTimeout(() => {
        completeAllSteps();

        // 隐藏加载动画，显示结果
        if (minutesLoadingContainer) {
            minutesLoadingContainer.style.display = 'none';
        }
        if (minutesResult) {
            minutesResult.style.display = 'block';
        }

        generateLocalMinutesContent(result, minutesResult);
    }, 3000); // 3秒后显示结果
}

function generateLocalMinutesContent(result, minutesResult) {
    const text = result.text || '';
    const utterances = result.utterances || [];

    if (text.length > 0) {
        // 生成Markdown格式的会议纪要
        let markdownContent = `# 会议纪要

## 会议基本信息

**会议名称：** 工作会议
**会议时间：** ${new Date().toLocaleDateString('zh-CN')}
**会议地点：** （未明确）

## 主要议题

`;

        // 生成主要议题
        const keyTopics = extractMainTopics(text, utterances);
        keyTopics.forEach((topic, index) => {
            markdownContent += `${index + 1}. ${topic}\n`;
        });

        markdownContent += `
## 详细讨论

`;

        if (utterances.length > 0) {
            utterances.forEach((utterance, index) => {
                const speaker = utterance.speaker_id || utterance.speaker || `发言人${index + 1}`;
                const time = formatDuration(utterance.start_time);
                markdownContent += `### [${time}] ${speaker}

${utterance.text}

`;
            });
        } else {
            markdownContent += `${text}

`;
        }

        // 生成会议总结
        const summaryPoints = generateMeetingSummary(text, utterances);
        markdownContent += `## 会议总结

`;
        summaryPoints.forEach(point => {
            markdownContent += `- ${point}\n`;
        });

        // 生成后续行动
        const actionItems = generateActionItems(text, utterances);
        markdownContent += `
## 后续行动

`;
        actionItems.forEach(item => {
            markdownContent += `- ${item}\n`;
        });

        // 使用marked.js渲染Markdown
        const htmlContent = marked.parse(markdownContent);
        minutesResult.innerHTML = htmlContent;

    } else {
        minutesResult.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">暂无会议内容记录</div>';
    }
}

// 旧的generateAIMeetingMinutes函数已删除，使用新的异步版本

function generateTaskId() {
    return 'task_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

// 真实API调用
async function realRecognition() {
    try {
        // 获取配置
        const config = {
            enable_itn: enableItn.checked,
            enable_punc: enablePunc.checked,
            enable_ddc: false,
            enable_speaker: enableSpeaker.checked,
            show_utterances: showUtterances.checked
        };

        let submitResponse;

        if (currentFile) {
            // 如果是本地文件，使用分块上传
            statusMessage.textContent = '正在上传音频文件...';
            const formData = new FormData();
            formData.append('audio_file', currentFile);
            formData.append('format', getAudioFormat());
            formData.append('config', JSON.stringify(config));

            // 使用标准上传API
            submitResponse = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
        } else {
            // 如果是URL，使用JSON提交
            const url = audioUrl.value.trim();
            if (!url) {
                showError('请输入音频URL或选择本地文件');
                return;
            }

            statusMessage.textContent = '正在提交识别任务...';
            submitResponse = await fetch('/api/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    audio_url: url,
                    format: getAudioFormat(),
                    config: config
                })
            });
        }

        const submitResult = await submitResponse.json();

        if (!submitResponse.ok || !submitResult.success) {
            // 特殊处理云存储不可用的情况
            if (submitResponse.status === 503 && submitResult.error) {
                throw new Error(submitResult.error + (submitResult.suggestion ? '\n\n' + submitResult.suggestion : ''));
            }
            throw new Error(submitResult.error || '提交任务失败');
        }

        currentTaskId = submitResult.task_id;
        taskId.textContent = currentTaskId;

        // 异步等待结果
        await pollForResult();

    } catch (error) {
        console.error('识别失败:', error);
        showError('识别失败: ' + error.message);
        updateUI('initial');
    }
}

// 异步等待结果（长轮询）
async function pollForResult() {
    const startTime = Date.now();

    try {
        statusMessage.textContent = '正在处理音频文件，请耐心等待...';
        progressFill.style.width = '10%';

        // 使用长轮询接口，设置较长的超时时间（30分钟）
        const response = await fetch(`/api/wait/${currentTaskId}?timeout=1800`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (!response.ok) {
            if (response.status === 404) {
                // 任务不存在
                const isLocalFile = currentFile !== null;
                let message = '任务不存在或已过期。\n\n';
                if (isLocalFile) {
                    message += '这通常是因为本地文件无法被远程API访问。\n\n' +
                             '解决方案：\n' +
                             '1. 使用云存储：将文件上传到阿里云OSS、腾讯云COS等\n' +
                             '2. 使用公开URL：直接使用可访问的音频链接\n' +
                             '3. 安装ngrok：创建本地隧道（技术用户）\n\n';
                }

                message += '建议您：\n\n' +
                         '1. 检查网络连接\n' +
                         '2. 尝试使用现场录音功能\n' +
                         '3. 查看详细说明';

                showDetailedSolution(isLocalFile);
                updateUI('initial');
                return;
            } else if (response.status === 408) {
                // 超时，但任务可能仍在处理 - 显示友好的提示而不是错误
                console.log('任务处理超时，但可能仍在后台处理');
                showProcessingTimeoutMessage(currentTaskId);
                return;
            } else {
                throw new Error(result.error || '查询失败');
            }
        }

        // 处理成功结果
        if (result.success && result.result) {
            // 识别完成
            progressFill.style.width = '100%';
            statusMessage.textContent = '识别完成！';

            const endTime = Date.now();
            const duration = Math.round((endTime - startTime) / 1000);

            displayResult(result.result, duration);
            updateUI('completed');

        } else {
            throw new Error('识别结果异常');
        }

    } catch (error) {
        console.error('识别失败:', error);

        // 特殊处理超时错误 - 已经在上面处理了，这里不需要弹窗
        if (!error.message.includes('处理时间较长')) {
            showError('识别过程出错: ' + error.message);
            updateUI('initial');
        }
    }
}

// 显示处理超时的友好消息
function showProcessingTimeoutMessage(taskId) {
    const statusMessage = document.getElementById('statusMessage');
    const progressContainer = document.getElementById('progressContainer');

    statusMessage.innerHTML = `
        <div style="color: #f56565; margin-bottom: 15px;">
            <i class="fas fa-clock"></i> 处理时间较长，任务仍在后台处理中...
        </div>
        <div style="color: #666; font-size: 14px; margin-bottom: 15px;">
            任务ID: ${taskId}
        </div>
        <div style="display: flex; gap: 10px; justify-content: center;">
            <button onclick="checkTaskManually('${taskId}')" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                手动查询结果
            </button>
            <button onclick="tryDemoMode()" style="background: #48bb78; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                尝试演示模式
            </button>
            <button onclick="location.reload()" style="background: #ed8936; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                重新开始
            </button>
        </div>
    `;

    // 隐藏进度条
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
}

// 手动查询任务结果
async function checkTaskManually(taskId) {
    try {
        const statusMessage = document.getElementById('statusMessage');
        statusMessage.textContent = '正在查询任务结果...';

        const response = await fetch(`/api/query/${taskId}`);
        const result = await response.json();

        if (result.success && result.is_success && result.result) {
            // 任务完成了！
            currentTaskId = taskId;
            displayResult(result.result);
            updateUI('completed');
        } else if (result.is_processing) {
            statusMessage.innerHTML = `
                <div style="color: #f56565;">
                    <i class="fas fa-spinner fa-spin"></i> 任务仍在处理中，请稍后再试
                </div>
                <div style="margin-top: 10px;">
                    <button onclick="checkTaskManually('${taskId}')" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        再次查询
                    </button>
                </div>
            `;
        } else {
            statusMessage.innerHTML = `
                <div style="color: #e53e3e;">
                    <i class="fas fa-exclamation-triangle"></i> 任务处理失败或不存在
                </div>
                <div style="margin-top: 10px;">
                    <button onclick="tryDemoMode()" style="background: #48bb78; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        尝试演示模式
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('手动查询失败:', error);
        showError('查询失败: ' + error.message);
    }
}

// 尝试演示模式
function tryDemoMode() {
    if (confirm('是否切换到演示模式？\n\n演示模式将使用预设的会议录音进行体验。')) {
        simulateRecognition();
    }
}

// 录音功能
function showRecordingInterface() {
    // 隐藏其他界面
    const welcomeSection = document.getElementById('welcomeSection');
    const transcriptionSection = document.getElementById('transcriptionSection');
    const statusSection = document.getElementById('statusSection');
    const meetingSummarySection = document.getElementById('meetingSummarySection');

    if (welcomeSection) welcomeSection.style.display = 'none';
    if (transcriptionSection) transcriptionSection.style.display = 'none';
    if (statusSection) statusSection.style.display = 'none';
    if (meetingSummarySection) meetingSummarySection.style.display = 'none';

    // 显示录音界面
    if (recordingSection) {
        recordingSection.style.display = 'block';
    }

    // 重置录音状态
    resetRecordingState();
}

function resetRecordingState() {
    recordedChunks = [];
    recordingStartTime = null;

    // 重置UI
    recordingStatus.querySelector('.status-text').textContent = '准备录音';
    recordingStatus.classList.remove('recording');
    recordingTime.textContent = '00:00';
    recordingSize.textContent = '0 KB';

    // 重置按钮状态
    startRecordBtn.style.display = 'block';
    pauseRecordBtn.style.display = 'none';
    stopRecordBtn.style.display = 'none';
    recordingActions.style.display = 'none';

    // 清理定时器
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }

    // 清理音频可视化
    if (visualizerAnimationId) {
        cancelAnimationFrame(visualizerAnimationId);
        visualizerAnimationId = null;
    }
}

async function startRecording() {
    try {
        // 请求麦克风权限
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 16000
            }
        });

        // 创建MediaRecorder - 尝试使用WAV格式
        let options = {
            mimeType: 'audio/wav',
            audioBitsPerSecond: 128000
        };

        // 如果不支持WAV，尝试WebM
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options.mimeType = 'audio/webm;codecs=opus';
        }

        // 如果还不支持，使用默认
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options = {};
        }

        mediaRecorder = new MediaRecorder(audioStream, options);

        // 设置事件处理器
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
                updateRecordingSize();
            }
        };

        mediaRecorder.onstop = () => {
            // 录音完成后的处理
            handleRecordingComplete();
        };

        // 开始录音
        recordedChunks = [];
        mediaRecorder.start(1000); // 每秒收集一次数据
        recordingStartTime = Date.now();

        // 更新UI
        recordingStatus.querySelector('.status-text').textContent = '正在录音...';
        recordingStatus.classList.add('recording');
        startRecordBtn.style.display = 'none';
        pauseRecordBtn.style.display = 'block';
        stopRecordBtn.style.display = 'block';

        // 显示录音指示器
        const indicator = document.getElementById('recordingIndicator');
        if (indicator) {
            indicator.classList.add('show');
        }

        // 开始计时器
        startRecordingTimer();

        // 开始音频可视化
        startAudioVisualization();

    } catch (error) {
        console.error('录音启动失败:', error);
        alert('无法访问麦克风，请检查权限设置');
    }
}

function pauseRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.pause();
        recordingStatus.querySelector('.status-text').textContent = '录音已暂停';
        recordingStatus.classList.remove('recording');
        pauseRecordBtn.innerHTML = '<i class="fas fa-play"></i> 继续录音';
    } else if (mediaRecorder && mediaRecorder.state === 'paused') {
        mediaRecorder.resume();
        recordingStatus.querySelector('.status-text').textContent = '正在录音...';
        recordingStatus.classList.add('recording');
        pauseRecordBtn.innerHTML = '<i class="fas fa-pause"></i> 暂停录音';
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }

    // 停止音频流
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }

    // 更新UI
    recordingStatus.querySelector('.status-text').textContent = '录音完成';
    recordingStatus.classList.remove('recording');
    startRecordBtn.style.display = 'block';
    pauseRecordBtn.style.display = 'none';
    stopRecordBtn.style.display = 'none';

    // 隐藏录音指示器
    const indicator = document.getElementById('recordingIndicator');
    if (indicator) {
        indicator.classList.remove('show');
    }

    // 停止计时器
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }

    // 停止音频可视化
    if (visualizerAnimationId) {
        cancelAnimationFrame(visualizerAnimationId);
        visualizerAnimationId = null;
    }

    // 清理可视化画布
    const canvas = audioVisualizer;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function startRecordingTimer() {
    recordingTimer = setInterval(() => {
        if (recordingStartTime) {
            const elapsed = Date.now() - recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            recordingTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

function updateRecordingSize() {
    const totalSize = recordedChunks.reduce((size, chunk) => size + chunk.size, 0);
    const sizeInKB = Math.round(totalSize / 1024);
    const sizeInMB = (totalSize / (1024 * 1024)).toFixed(2);

    if (totalSize < 1024 * 1024) {
        recordingSize.textContent = `${sizeInKB} KB`;
    } else {
        recordingSize.textContent = `${sizeInMB} MB`;
    }
}

function startAudioVisualization() {
    if (!audioStream) return;

    // 创建音频上下文
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(audioStream);
    source.connect(analyser);

    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const canvas = audioVisualizer;
    const ctx = canvas.getContext('2d');

    function draw() {
        if (!analyser) return;

        visualizerAnimationId = requestAnimationFrame(draw);

        analyser.getByteFrequencyData(dataArray);

        ctx.fillStyle = '#f7fafc';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            barHeight = (dataArray[i] / 255) * canvas.height * 0.8;

            const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
            gradient.addColorStop(0, '#667eea');
            gradient.addColorStop(1, '#764ba2');

            ctx.fillStyle = gradient;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

            x += barWidth + 1;
        }
    }

    draw();
}

function handleRecordingComplete() {
    // 显示录音操作按钮
    recordingActions.style.display = 'flex';
}

function playRecording() {
    if (recordedChunks.length === 0) return;

    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);

    audio.play().catch(error => {
        console.error('播放录音失败:', error);
        alert('播放录音失败');
    });

    // 播放完成后清理URL
    audio.addEventListener('ended', () => {
        URL.revokeObjectURL(audioUrl);
    });
}

async function uploadRecording() {
    if (recordedChunks.length === 0) {
        alert('没有录音数据');
        return;
    }

    try {
        // 创建音频文件 - 检测实际的MIME类型
        let mimeType = 'audio/wav';
        let extension = 'wav';

        if (recordedChunks.length > 0 && recordedChunks[0].type) {
            mimeType = recordedChunks[0].type;
            if (mimeType.includes('webm')) {
                extension = 'webm';
            } else if (mimeType.includes('wav')) {
                extension = 'wav';
            } else if (mimeType.includes('mp3')) {
                extension = 'mp3';
            }
        }

        const blob = new Blob(recordedChunks, { type: mimeType });
        const file = new File([blob], `recording_${Date.now()}.${extension}`, { type: mimeType });

        // 设置当前文件
        currentFile = file;

        // 隐藏录音界面，显示处理界面
        recordingSection.style.display = 'none';

        // 开始处理
        updateUI('processing');
        await handleFileUpload(file);

    } catch (error) {
        console.error('上传录音失败:', error);
        alert('上传录音失败: ' + error.message);
    }
}

// 处理文件上传
async function handleFileUpload(file) {
    try {
        // 获取配置
        const config = {
            enable_itn: enableItn.checked,
            enable_punc: enablePunc.checked,
            enable_ddc: false,
            enable_speaker: enableSpeaker.checked,
            show_utterances: showUtterances.checked
        };

        statusMessage.textContent = '正在上传录音文件...';

        const formData = new FormData();
        formData.append('file', file);  // 使用'file'字段名

        // 根据文件类型设置格式
        let format = 'wav';
        if (file.type.includes('webm')) {
            format = 'webm';
        } else if (file.type.includes('mp3')) {
            format = 'mp3';
        }

        formData.append('format', format);
        formData.append('config', JSON.stringify(config));

        // 使用标准上传API
        let submitResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const result = await submitResponse.json();

        if (!submitResponse.ok) {
            // 特殊处理云存储不可用的情况
            if (submitResponse.status === 503 && result.error) {
                throw new Error(result.error + (result.suggestion ? '\n\n' + result.suggestion : ''));
            }
            throw new Error(result.error || `HTTP ${submitResponse.status}: ${submitResponse.statusText}`);
        }

        if (!result.success) {
            throw new Error(result.error || '上传失败');
        }

        currentTaskId = result.task_id;
        statusMessage.textContent = '录音上传成功，正在处理...';

        // 开始等待结果
        await pollForResult();

    } catch (error) {
        console.error('文件上传失败:', error);
        showError('录音上传失败: ' + error.message);
        updateUI('initial');
    }
}

function discardRecording() {
    if (confirm('确定要丢弃当前录音吗？')) {
        resetRecordingState();
    }
}

// 获取音频格式
function getAudioFormat() {
    if (currentFile) {
        const fileName = currentFile.name.toLowerCase();
        if (fileName.endsWith('.mp3')) return 'mp3';
        if (fileName.endsWith('.wav')) return 'wav';
        if (fileName.endsWith('.ogg')) return 'ogg';
        if (fileName.endsWith('.raw')) return 'raw';
        if (fileName.endsWith('.aiff')) return 'wav'; // AIFF转换为WAV格式处理
        if (fileName.endsWith('.m4a')) return 'mp3'; // M4A转换为MP3格式处理
        return 'wav'; // 默认
    } else {
        const url = audioUrl.value.toLowerCase();
        if (url.includes('.wav')) return 'wav';
        if (url.includes('.ogg')) return 'ogg';
        if (url.includes('.raw')) return 'raw';
        if (url.includes('.mp3')) return 'mp3';
        if (url.includes('.aiff')) return 'wav';
        if (url.includes('.m4a')) return 'mp3';
        return 'wav'; // 默认使用wav格式
    }
}

function showError(message) {
    // 创建更好的错误提示
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fed7d7;
        color: #c53030;
        padding: 16px 20px;
        border-radius: 8px;
        border: 1px solid #feb2b2;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 1000;
        max-width: 400px;
        font-size: 14px;
        line-height: 1.4;
    `;
    errorDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(errorDiv);

    // 3秒后自动移除
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 3000);
}

// 显示详细解决方案
function showDetailedSolution(isLocalFile) {
    const statusDiv = document.getElementById('status');
    const statusSection = document.getElementById('statusSection');

    // 隐藏状态卡片，显示解决方案
    statusSection.style.display = 'none';
    statusDiv.style.display = 'block';

    let solutionHtml = `
        <div class="solution-guide">
            <h3><i class="fas fa-lightbulb"></i> 解决方案指南</h3>
    `;

    if (isLocalFile) {
        solutionHtml += `
            <div class="solution-section">
                <h4>🔧 本地文件上传问题</h4>
                <p>本地文件无法被远程API直接访问，需要使用以下方案：</p>

                <div class="solution-option">
                    <h5>方案1：使用云存储服务</h5>
                    <ul>
                        <li>阿里云OSS：<a href="https://oss.console.aliyun.com" target="_blank">https://oss.console.aliyun.com</a></li>
                        <li>腾讯云COS：<a href="https://console.cloud.tencent.com/cos" target="_blank">https://console.cloud.tencent.com/cos</a></li>
                        <li>七牛云：<a href="https://portal.qiniu.com" target="_blank">https://portal.qiniu.com</a></li>
                    </ul>
                </div>

                <div class="solution-option">
                    <h5>方案2：使用ngrok创建隧道</h5>
                    <pre>brew install ngrok
ngrok http 8080</pre>
                    <p>然后使用ngrok提供的公开URL</p>
                </div>
            </div>
        `;
    }

    solutionHtml += `
            <div class="solution-section">
                <h4>🌐 推荐测试URL</h4>
                <div class="test-urls">
                    <div class="url-item">
                        <strong>示例音频：</strong>
                        <input type="text" value="https://file-examples.com/storage/fe68c1e7b1b66fe3dbf1af4/2017/11/file_example_WAV_1MG.wav" readonly onclick="this.select()">
                        <button onclick="testWithUrl('https://file-examples.com/storage/fe68c1e7b1b66fe3dbf1af4/2017/11/file_example_WAV_1MG.wav')">测试此URL</button>
                    </div>
                </div>
            </div>

            <div class="solution-actions">
                <button onclick="hideSolution()" class="btn-secondary">返回上传</button>
                <button onclick="showRecordingInterface()" class="btn-primary">现场录音</button>
            </div>
        </div>
    `;

    statusDiv.innerHTML = solutionHtml;
}

// 隐藏解决方案
function hideSolution() {
    const statusDiv = document.getElementById('status');
    statusDiv.style.display = 'none';
    updateUI('initial');
}

// 使用指定URL进行测试
function testWithUrl(url) {
    document.getElementById('audioUrl').value = url;
    updateUI('initial');
    // 滚动到URL输入区域
    document.getElementById('audioUrl').scrollIntoView({ behavior: 'smooth' });
}

// 任务历史功能
function initializeTaskHistory() {
    const historyBtn = document.getElementById('historyBtn');
    const historyModal = document.getElementById('historyModal');
    const closeHistoryModal = document.getElementById('closeHistoryModal');
    const queryTaskBtn = document.getElementById('queryTaskBtn');
    const taskIdInput = document.getElementById('taskIdInput');
    const taskResultSection = document.getElementById('taskResultSection');
    const taskResult = document.getElementById('taskResult');

    if (!historyBtn || !historyModal) return; // 如果元素不存在则退出

    // 打开历史弹窗
    historyBtn.addEventListener('click', () => {
        historyModal.style.display = 'flex';
    });

    // 关闭历史弹窗
    closeHistoryModal.addEventListener('click', () => {
        historyModal.style.display = 'none';
    });

    // 点击背景关闭弹窗
    historyModal.addEventListener('click', (e) => {
        if (e.target === historyModal) {
            historyModal.style.display = 'none';
        }
    });

    // 查询特定任务
    queryTaskBtn.addEventListener('click', async () => {
        const taskId = taskIdInput.value.trim();
        if (!taskId) {
            alert('请输入任务ID');
            return;
        }
        await queryTaskStatus(taskId);
    });

    // 为已知任务添加查询按钮事件
    document.querySelectorAll('.task-action-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const taskItem = e.target.closest('.task-item');
            const taskId = taskItem.dataset.taskId;
            await queryTaskStatus(taskId);
        });
    });

    // 查询任务状态
    async function queryTaskStatus(taskId) {
        try {
            taskResult.textContent = '正在查询...';
            taskResultSection.style.display = 'block';

            const response = await fetch(`/api/query/${taskId}`);
            const result = await response.json();

            if (response.ok && result.success) {
                if (result.is_success && result.result) {
                    // 任务已完成
                    const audioInfo = result.result.audio_info || {};
                    const utterances = result.result.utterances || [];

                    taskResult.textContent = `✅ 任务已完成！

识别文本：
${result.result.text}

音频信息：
- 时长: ${audioInfo.duration || 'N/A'}秒
- 采样率: ${audioInfo.sample_rate || 'N/A'}Hz
- 声道数: ${audioInfo.channels || 'N/A'}

分句数量: ${utterances.length}

状态码: ${result.status_code}
消息: ${result.message}`;

                    // 提供使用此结果的选项
                    const useResult = confirm('任务已完成！是否使用此结果生成会议纪要？');
                    if (useResult) {
                        historyModal.style.display = 'none';
                        // 设置当前任务ID并显示结果
                        currentTaskId = taskId;

                        // 计算处理时间（模拟）
                        const processTime = Math.floor(Math.random() * 300) + 60; // 60-360秒

                        displayResult(result.result, processTime);
                        updateUI('completed');

                        // 自动生成会议纪要
                        generateMeetingMinutes(taskId, result.result);
                    }
                } else if (result.is_processing) {
                    // 任务处理中
                    taskResult.textContent = `⏳ 任务处理中...

状态码: ${result.status_code}
消息: ${result.message}

任务ID: ${taskId}

您可以：
1. 继续等待处理完成
2. 使用长轮询等待结果`;

                    const waitForResult = confirm('任务仍在处理中。是否使用长轮询等待结果？');
                    if (waitForResult) {
                        historyModal.style.display = 'none';
                        currentTaskId = taskId;
                        updateUI('processing');
                        await pollForResult();
                    }
                } else if (result.is_failed) {
                    // 任务失败
                    taskResult.textContent = `❌ 任务失败

状态码: ${result.status_code}
消息: ${result.message}

任务ID: ${taskId}`;
                } else {
                    // 其他状态
                    taskResult.textContent = `📋 任务状态

状态码: ${result.status_code}
消息: ${result.message}
处理中: ${result.is_processing}
已完成: ${result.is_success}
已失败: ${result.is_failed}

任务ID: ${taskId}`;
                }
            } else {
                taskResult.textContent = `❌ 查询失败

错误: ${result.error || '未知错误'}

任务ID: ${taskId}

可能原因：
1. 任务ID不存在
2. 任务已过期
3. 网络连接问题`;
            }
        } catch (error) {
            taskResult.textContent = `❌ 查询出错

错误: ${error.message}

任务ID: ${taskId}`;
        }
    }
}

// 异步生成会议纪要
async function generateMeetingMinutes(taskId, asrResult) {
    try {
        // 隐藏欢迎页面
        const welcomeSection = document.getElementById('welcomeSection');
        if (welcomeSection) {
            welcomeSection.style.display = 'none';
        }

        // 显示生成中状态
        const meetingMinutesSection = document.getElementById('meetingMinutesSection');
        const minutesContent = document.getElementById('minutesContent');
        const keyInfoSection = document.getElementById('keyInfoSection');
        const speakersSection = document.getElementById('speakersSection');
        const aiToolsSection = document.getElementById('aiToolsSection');

        if (meetingMinutesSection) {
            meetingMinutesSection.style.display = 'block';

            // 显示加载动画，隐藏结果区域
            const minutesLoadingContainer = document.getElementById('minutesLoadingContainer');
            const minutesResult = document.getElementById('minutesResult');

            if (minutesLoadingContainer) {
                minutesLoadingContainer.style.display = 'flex';
            }
            if (minutesResult) {
                minutesResult.style.display = 'none';
            }

            // 开始步骤动画
            startLoadingSteps();
        }

        // 提交异步任务
        const submitResponse = await fetch(`/api/generate_minutes/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                focus_last_speakers: true,
                speaker_count: 2,
                topic: '工作会议',
                date: new Date().toLocaleDateString('zh-CN'),
                host: '党委书记',
                attendees: ['总经理', '相关部门负责人']
            })
        });

        const submitResult = await submitResponse.json();

        if (submitResponse.ok && submitResult.success) {
            const asyncTaskId = submitResult.async_task_id;

            // 保存异步任务ID到全局变量，供Word下载使用
            window.currentAsyncTaskId = asyncTaskId;

            updateMinutesStatus('任务已提交，开始AI生成...', 10);

            // 开始轮询任务状态
            pollAsyncTaskStatus(asyncTaskId, minutesContent, keyInfoSection, speakersSection, aiToolsSection);

        } else {
            throw new Error(submitResult.error || '提交任务失败');
        }

    } catch (error) {
        console.error('生成会议纪要失败:', error);
        const minutesContent = document.getElementById('minutesContent');
        if (minutesContent) {
            minutesContent.innerHTML = `<div style="color: #e53e3e; text-align: center; padding: 20px;">
                <i class="fas fa-exclamation-triangle"></i>
                网络错误，无法生成会议纪要：${error.message}
            </div>`;
        }
    }
}

// 轮询异步任务状态
async function pollAsyncTaskStatus(asyncTaskId, minutesContent, keyInfoSection, speakersSection, aiToolsSection) {
    const maxAttempts = 900; // 最多轮询900次（30分钟）
    const maxConsecutiveFailures = 10; // 最多连续失败10次
    let attempts = 0;
    let consecutiveFailures = 0;

    // 检查是否是已知的过期任务ID
    const knownExpiredTasks = [
        'minutes_08b2fee3-31d7-4ceb-b208-17e7b74392d1',
        'minutes_de23e3c0-b546-47bd-843c-11ec1580e551'
    ];

    if (knownExpiredTasks.includes(asyncTaskId)) {
        console.log('检测到已知过期任务，立即停止轮询:', asyncTaskId);
        showMinutesError('任务已过期，请重新生成会议纪要');
        return;
    }

    const pollInterval = setInterval(async () => {
        attempts++;

        try {
            // 查询任务状态
            const statusResponse = await fetch(`/api/async_task/${asyncTaskId}`);
            const statusResult = await statusResponse.json();

            if (statusResponse.ok && statusResult.success) {
                // 重置连续失败计数器
                consecutiveFailures = 0;

                const taskStatus = statusResult.task_status;
                const progress = taskStatus.progress || 0;
                const status = taskStatus.status;

                // 更新进度和状态
                updateMinutesProgress(progress);

                if (status === 'pending') {
                    updateMinutesStatus('任务排队中...', progress);
                } else if (status === 'running') {
                    updateMinutesStatus('AI正在分析会议内容...', progress);
                } else if (status === 'completed') {
                    clearInterval(pollInterval);
                    updateMinutesStatus('生成完成，正在获取结果...', 95);

                    // 获取任务结果
                    await getAsyncTaskResult(asyncTaskId, minutesContent, keyInfoSection, speakersSection, aiToolsSection);

                } else if (status === 'failed') {
                    clearInterval(pollInterval);
                    const error = taskStatus.error || '任务执行失败';
                    showMinutesError(`AI生成失败：${error}`);
                }

            } else {
                consecutiveFailures++;

                // 检查是否是任务不存在的错误
                if (statusResult.error && statusResult.error.includes('任务不存在')) {
                    clearInterval(pollInterval);
                    showMinutesError('任务已过期或不存在，请重新生成会议纪要');
                    return;
                }

                // 如果连续失败次数过多，停止轮询
                if (consecutiveFailures >= maxConsecutiveFailures) {
                    clearInterval(pollInterval);
                    showMinutesError('任务查询连续失败，请重新生成会议纪要');
                    return;
                }

                throw new Error(statusResult.error || '查询状态失败');
            }

        } catch (error) {
            consecutiveFailures++;
            console.error('查询任务状态失败:', error);

            // 检查是否是网络错误或任务不存在
            if (error.message && error.message.includes('任务不存在')) {
                clearInterval(pollInterval);
                showMinutesError('任务已过期或不存在，请重新生成会议纪要');
                return;
            }

            // 如果连续失败次数过多，停止轮询
            if (consecutiveFailures >= maxConsecutiveFailures) {
                clearInterval(pollInterval);
                showMinutesError('任务查询连续失败，请重新生成会议纪要');
                return;
            }

            if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                showMinutesError('任务超时，请稍后重试');
            }
        }

        // 超时处理
        if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            showMinutesError('任务超时，请稍后重试');
        }

    }, 2000); // 每2秒查询一次
}

// 获取异步任务结果
async function getAsyncTaskResult(asyncTaskId, minutesContent, keyInfoSection, speakersSection, aiToolsSection) {
    try {
        const resultResponse = await fetch(`/api/async_task/${asyncTaskId}/result`);
        const result = await resultResponse.json();

        if (resultResponse.ok && result.success) {
            updateMinutesProgress(100);
            updateMinutesStatus('生成完成！', 100);

            // 延迟一下再显示结果，让用户看到完成状态
            setTimeout(() => {
                displayMeetingMinutesResult(result.minutes_data, minutesContent, keyInfoSection, speakersSection, aiToolsSection);
            }, 500);

        } else {
            throw new Error(result.error || '获取结果失败');
        }

    } catch (error) {
        console.error('获取任务结果失败:', error);
        showMinutesError(`获取结果失败：${error.message}`);
    }
}

// 更新会议纪要生成进度
function updateMinutesProgress(progress) {
    const progressBar = document.getElementById('minutesProgressBar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
}

// 更新会议纪要生成状态文本
function updateMinutesStatus(statusText, progress) {
    const statusTextElement = document.getElementById('minutesStatusText');
    if (statusTextElement) {
        statusTextElement.textContent = `${statusText} (${progress}%)`;
    }
}

// 显示会议纪要错误
function showMinutesError(errorMessage) {
    // 清理全局状态
    window.currentAsyncTaskId = null;

    // 隐藏加载动画
    const minutesLoadingContainer = document.getElementById('minutesLoadingContainer');
    const minutesResult = document.getElementById('minutesResult');

    if (minutesLoadingContainer) {
        minutesLoadingContainer.style.display = 'none';
    }

    if (minutesResult) {
        minutesResult.style.display = 'block';
        minutesResult.innerHTML = `
            <div style="color: #e53e3e; text-align: center; padding: 30px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 16px;"></i>
                <h3 style="margin-bottom: 8px;">生成失败</h3>
                <p style="margin-bottom: 20px;">${errorMessage}</p>
                <button onclick="location.reload()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    重新尝试
                </button>
            </div>
        `;
    }
}

// 过滤思考部分的函数
function filterThinkingSection(content) {
    if (!content) return content;

    // 移除<思考>...</思考>部分（包括换行符）
    return content.replace(/<思考>[\s\S]*?<\/思考>\s*/g, '').trim();
}

// 显示会议纪要结果
function displayMeetingMinutesResult(minutesData, minutesContent, keyInfoSection, speakersSection, aiToolsSection) {
    try {
        // 确保异步任务ID可用（如果还没有设置的话）
        if (!window.currentAsyncTaskId && minutesData?.async_task_id) {
            window.currentAsyncTaskId = minutesData.async_task_id;
        }

        // 完成所有步骤
        completeAllSteps();

        // 隐藏加载动画，显示结果
        const minutesLoadingContainer = document.getElementById('minutesLoadingContainer');
        const minutesResult = document.getElementById('minutesResult');

        if (minutesLoadingContainer) {
            minutesLoadingContainer.style.display = 'none';
        }
        if (minutesResult) {
            minutesResult.style.display = 'block';
        }

        // 显示会议纪要主要内容
        if (minutesResult && minutesData?.content?.summary) {
            let markdownContent = minutesData.content.summary;

            // 过滤掉<思考>部分
            markdownContent = filterThinkingSection(markdownContent);

            const htmlContent = marked.parse(markdownContent);
            minutesResult.innerHTML = htmlContent;
        }

        // 显示关键信息
        if (keyInfoSection && minutesData?.content) {
            keyInfoSection.style.display = 'block';
            const content = minutesData.content;

            const decisionsElement = document.getElementById('decisionsContent');
            const actionsElement = document.getElementById('actionsContent');
            const responsibilitiesElement = document.getElementById('responsibilitiesContent');
            const deadlinesElement = document.getElementById('deadlinesContent');

            if (decisionsElement) {
                decisionsElement.textContent = content.decisions?.join(', ') || '无';
            }
            if (actionsElement) {
                actionsElement.textContent = content.action_items?.join(', ') || '无';
            }
            if (responsibilitiesElement) {
                responsibilitiesElement.textContent = content.responsibilities?.join(', ') || '无';
            }
            if (deadlinesElement) {
                deadlinesElement.textContent = content.deadlines?.join(', ') || '无';
            }
        }

        // 显示重点发言人
        if (speakersSection && minutesData?.content?.leadership_remarks) {
            speakersSection.style.display = 'block';
            const speakersContent = document.getElementById('speakersContent');
            if (speakersContent) {
                speakersContent.innerHTML = '';

                const remarks = minutesData.content.leadership_remarks;
                Object.entries(remarks).forEach(([speaker, content]) => {
                    const speakerDiv = document.createElement('div');
                    speakerDiv.className = 'speaker-item';
                    speakerDiv.innerHTML = `
                        <div class="speaker-name">${speaker}</div>
                        <div class="speaker-content">${content}</div>
                    `;
                    speakersContent.appendChild(speakerDiv);
                });
            }
        }

        // 显示AI工具
        if (aiToolsSection) {
            aiToolsSection.style.display = 'block';
        }

        // 启用Word下载按钮
        setWordDownloadButtonState(true);

        console.log('会议纪要显示完成');

    } catch (error) {
        console.error('显示会议纪要结果失败:', error);
        showMinutesError('显示结果时出错');
    }
}

// 初始化配置项
function initializeConfigItems() {
    const configItems = document.querySelectorAll('.config-item');

    configItems.forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');

        // 设置初始状态
        updateConfigItemState(item, checkbox.checked);

        // 监听开关变化
        checkbox.addEventListener('change', function() {
            updateConfigItemState(item, this.checked);
        });
    });
}

// 更新配置项状态
function updateConfigItemState(item, isActive) {
    if (isActive) {
        item.classList.add('active');
    } else {
        item.classList.remove('active');
    }
}

// 初始化转录记录收缩功能
function initializeTranscriptionCollapse() {
    const collapseBtn = document.getElementById('transcriptionCollapseBtn');
    const transcriptionSection = document.getElementById('transcriptionSection');

    if (collapseBtn && transcriptionSection) {
        collapseBtn.addEventListener('click', function() {
            transcriptionSection.classList.toggle('collapsed');

            // 更新按钮图标
            const icon = collapseBtn.querySelector('i');
            if (transcriptionSection.classList.contains('collapsed')) {
                icon.className = 'fas fa-chevron-down';
                collapseBtn.classList.add('collapsed');
            } else {
                icon.className = 'fas fa-chevron-up';
                collapseBtn.classList.remove('collapsed');
            }
        });
    }
}

// 步骤动画控制函数
function startLoadingSteps() {
    // 重置所有步骤
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => {
        step.classList.remove('active', 'completed');
        const icon = step.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-circle';
        }
    });

    // 激活第一步
    const step1 = document.getElementById('step1');
    if (step1) {
        step1.classList.add('active');
        const icon = step1.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-circle';
        }
    }

    // 5秒后激活第二步
    setTimeout(() => {
        completeStep('step1');
        activateStep('step2');
    }, 5000);

    // 15秒后激活第三步
    setTimeout(() => {
        completeStep('step2');
        activateStep('step3');
    }, 15000);
}

function activateStep(stepId) {
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.add('active');
        const icon = step.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-circle';
        }
    }
}

function completeStep(stepId) {
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.remove('active');
        step.classList.add('completed');
        const icon = step.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-check-circle';
        }
    }
}

function completeAllSteps() {
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => {
        step.classList.remove('active');
        step.classList.add('completed');
        const icon = step.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-check-circle';
        }
    });
}

// ==================== 系统设置功能 ====================

// 打开设置弹窗
function openSettings() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'flex';

    // 加载当前配置
    loadSettings();
}

// 关闭设置弹窗
function closeSettings() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'none';
}

// 切换设置标签
function switchTab(tabName) {
    // 更新标签按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // 更新面板显示
    document.querySelectorAll('.settings-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(`${tabName}-panel`).classList.add('active');
}

// 加载设置
async function loadSettings() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();

        if (data.success) {
            currentSettings = data.config;
            populateSettingsForm(data.config);
        } else {
            showMessage('加载配置失败: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('加载配置失败:', error);
        showMessage('加载配置失败: ' + error.message, 'error');
    }
}

// 填充设置表单
function populateSettingsForm(config) {
    // AI配置
    if (config.ai) {
        document.getElementById('arkApiKey').value = config.ai.ark_api_key || '';
        document.getElementById('arkModel').value = config.ai.ark_model || '';
        document.getElementById('arkBaseUrl').value = config.ai.ark_base_url || '';
        document.getElementById('arkTimeout').value = config.ai.ark_timeout || '';
    }

    // 存储配置
    if (config.storage) {
        document.getElementById('tosAccessKey').value = config.storage.tos_access_key || '';
        document.getElementById('tosSecretKey').value = config.storage.tos_secret_key || '';
        document.getElementById('tosBucket').value = config.storage.tos_bucket || '';
        document.getElementById('tosRegion').value = config.storage.tos_region || '';
        document.getElementById('maxFileSize').value = config.storage.max_file_size || '';
    }

    // ASR配置
    if (config.asr) {
        document.getElementById('asrAppKey').value = config.asr.asr_app_key || '';
        document.getElementById('asrAccessKey').value = config.asr.asr_access_key || '';
        document.getElementById('asrModel').value = config.asr.asr_model || '';
        document.getElementById('asrTimeout').value = config.asr.asr_timeout || '';
    }

    // 提示词配置
    if (config.prompt) {
        document.getElementById('systemPrompt').value = config.prompt.system_prompt || '';
        document.getElementById('glossary').value = config.prompt.glossary || '';
    }

    // 系统配置
    if (config.system) {
        document.getElementById('workerThreads').value = config.system.worker_threads || '';
        document.getElementById('logLevel').value = config.system.log_level || '';
        document.getElementById('minutesTemplate').value = config.system.minutes_template || '';
    }
}

// 保存设置
async function saveSettings() {
    try {
        // 收集所有配置
        const configs = {
            ai: {
                ark_api_key: document.getElementById('arkApiKey').value,
                ark_model: document.getElementById('arkModel').value,
                ark_base_url: document.getElementById('arkBaseUrl').value,
                ark_timeout: parseInt(document.getElementById('arkTimeout').value) || 300
            },
            storage: {
                tos_access_key: document.getElementById('tosAccessKey').value,
                tos_secret_key: document.getElementById('tosSecretKey').value,
                tos_bucket: document.getElementById('tosBucket').value,
                tos_region: document.getElementById('tosRegion').value,
                max_file_size: parseInt(document.getElementById('maxFileSize').value) || 500
            },
            asr: {
                asr_app_key: document.getElementById('asrAppKey').value,
                asr_access_key: document.getElementById('asrAccessKey').value,
                asr_model: document.getElementById('asrModel').value,
                asr_timeout: parseInt(document.getElementById('asrTimeout').value) || 1800
            },
            prompt: {
                system_prompt: document.getElementById('systemPrompt').value,
                glossary: document.getElementById('glossary').value
            },
            system: {
                worker_threads: parseInt(document.getElementById('workerThreads').value) || 2,
                log_level: document.getElementById('logLevel').value,
                minutes_template: document.getElementById('minutesTemplate').value
            }
        };

        // 逐个保存配置节
        for (const [section, config] of Object.entries(configs)) {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    section: section,
                    config: config
                })
            });

            const data = await response.json();
            if (!data.success) {
                throw new Error(`保存${section}配置失败: ${data.error}`);
            }
        }

        showMessage('配置保存成功！', 'success');
        closeSettings();

    } catch (error) {
        console.error('保存配置失败:', error);
        showMessage('保存配置失败: ' + error.message, 'error');
    }
}

// 重置设置
async function resetSettings() {
    if (!confirm('确定要重置所有配置为默认值吗？此操作不可撤销。')) {
        return;
    }

    try {
        const response = await fetch('/api/config/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        if (data.success) {
            showMessage('配置重置成功！', 'success');
            loadSettings(); // 重新加载配置
        } else {
            showMessage('配置重置失败: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('重置配置失败:', error);
        showMessage('重置配置失败: ' + error.message, 'error');
    }
}

// 显示消息提示
function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-toast message-${type}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    // 添加样式
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 400px;
        word-wrap: break-word;
    `;

    // 设置背景色
    if (type === 'success') {
        messageDiv.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
    } else if (type === 'error') {
        messageDiv.style.background = 'linear-gradient(135deg, #dc3545, #e74c3c)';
    } else {
        messageDiv.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
    }

    // 添加到页面
    document.body.appendChild(messageDiv);

    // 显示动画
    setTimeout(() => {
        messageDiv.style.transform = 'translateX(0)';
    }, 100);

    // 自动隐藏
    setTimeout(() => {
        messageDiv.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 300);
    }, 3000);
}

// 点击弹窗外部关闭
document.addEventListener('click', function(event) {
    const modal = document.getElementById('settingsModal');
    if (event.target === modal) {
        closeSettings();
    }
});

// 文本选择工具栏功能
let selectedText = '';
let selectedRange = null;
let toolbarVisible = false;

// 初始化文本选择工具栏 - 简化版本
function initializeTextSelectionToolbar() {
    const minutesContent = document.getElementById('minutesContent');
    const toolbar = document.getElementById('textSelectionToolbar');

    if (!minutesContent || !toolbar) return;

    // 简单的mouseup事件处理
    document.addEventListener('mouseup', function(e) {
        // 如果点击的是工具栏，不处理
        if (toolbar.contains(e.target)) return;

        // 延迟处理，让选择稳定
        setTimeout(() => {
            const selection = window.getSelection();
            const selectedText = selection.toString().trim();

            if (selectedText.length > 0 && isSelectionInMinutes()) {
                showToolbar(selection);
            } else {
                hideToolbar();
            }
        }, 50);
    });

    // 绑定工具栏按钮事件
    bindToolbarEvents();
}

// 处理文本选择
function handleTextSelection() {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    console.log('处理文本选择:', selectedText.length > 0 ? `"${selectedText}"` : '无选择');

    if (selectedText.length > 0 && isSelectionInMinutes()) {
        console.log('显示工具栏');
        showToolbar(selection);
    } else {
        console.log('隐藏工具栏');
        hideToolbar();
    }
}

// 检查选择是否在会议纪要区域内
function isSelectionInMinutes(target = null) {
    const minutesResult = document.getElementById('minutesResult');
    if (!minutesResult) return false;

    const selection = window.getSelection();
    if (selection.rangeCount === 0) return false;

    const range = selection.getRangeAt(0);
    return minutesResult.contains(range.commonAncestorContainer) ||
           minutesResult.contains(range.startContainer) ||
           minutesResult.contains(range.endContainer);
}

// 显示工具栏
function showToolbar(selection) {
    const toolbar = document.getElementById('textSelectionToolbar');
    if (!toolbar || !selection || selection.rangeCount === 0) return;

    selectedText = selection.toString().trim();
    selectedRange = selection.getRangeAt(0).cloneRange();

    // 获取选择区域的位置（相对于视口）
    const rect = selection.getRangeAt(0).getBoundingClientRect();

    // 工具栏尺寸
    const toolbarWidth = 240;
    const toolbarHeight = 280;

    // 计算工具栏位置（相对于页面）
    let left = rect.left + window.scrollX + (rect.width / 2) - (toolbarWidth / 2);
    let top = rect.top + window.scrollY - toolbarHeight - 8;

    // 水平边界检查
    const viewportWidth = window.innerWidth;
    if (left < 10) {
        left = 10;
    } else if (left + toolbarWidth > viewportWidth - 10) {
        left = viewportWidth - toolbarWidth - 10;
    }

    // 垂直边界检查 - 如果上方空间不够，显示在下方
    if (top < window.scrollY + 10) {
        top = rect.bottom + window.scrollY + 8;
    }

    // 设置为固定定位，相对于视口
    toolbar.style.position = 'fixed';
    toolbar.style.left = (left - window.scrollX) + 'px';
    toolbar.style.top = (top - window.scrollY) + 'px';
    toolbar.style.display = 'block';
    toolbar.style.zIndex = '9999';
    toolbarVisible = true;

    console.log('工具栏位置:', {
        选择区域: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
        工具栏位置: { left: left - window.scrollX, top: top - window.scrollY }
    });

    // 设置输入框事件处理
    setupInputEventHandlers();
}

// 隐藏工具栏
function hideToolbar() {
    const toolbar = document.getElementById('textSelectionToolbar');
    if (!toolbar || !toolbarVisible) return;

    toolbar.style.display = 'none';
    toolbarVisible = false;
    selectedText = '';
    selectedRange = null;
}

// 绑定工具栏事件
function bindToolbarEvents() {
    // AI扩写
    document.getElementById('aiExpandBtn')?.addEventListener('click', () => {
        processTextWithAI('expand', '请对以下内容进行扩写，使其更加详细和丰富：');
    });

    // 改进写作
    document.getElementById('aiImproveBtn')?.addEventListener('click', () => {
        processTextWithAI('improve', '请改进以下文本的写作质量，使其更加清晰、准确和专业：');
    });

    // 总结
    document.getElementById('aiSummarizeBtn')?.addEventListener('click', () => {
        processTextWithAI('summarize', '请总结以下内容的要点：');
    });

    // 检查拼写和语法
    document.getElementById('checkGrammarBtn')?.addEventListener('click', () => {
        processTextWithAI('grammar', '请检查并修正以下文本的拼写和语法错误：');
    });

    // 简化内容
    document.getElementById('simplifyBtn')?.addEventListener('click', () => {
        processTextWithAI('simplify', '请简化以下内容，使其更加简洁明了：');
    });

    // 丰富内容
    document.getElementById('formalizeBtn')?.addEventListener('click', () => {
        processTextWithAI('formalize', '请丰富以下内容，使其更加正式和专业：');
    });

    // 翻译
    document.getElementById('translateBtn')?.addEventListener('click', () => {
        processTextWithAI('translate', '请将以下内容翻译成英语：');
    });

    // 解释
    document.getElementById('explainBtn')?.addEventListener('click', () => {
        processTextWithAI('explain', '请解释以下内容的含义：');
    });

    // 自定义提示
    document.getElementById('customPromptBtn')?.addEventListener('click', () => {
        const customPrompt = document.getElementById('customPromptInput')?.value.trim();
        if (customPrompt) {
            processTextWithAI('custom', customPrompt + '：');
            document.getElementById('customPromptInput').value = '';
        }
    });

    // 自定义提示输入框回车事件
    document.getElementById('customPromptInput')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('customPromptBtn')?.click();
        }
    });
}

// 使用AI处理文本
async function processTextWithAI(action, prompt) {
    if (!selectedText || !selectedRange) {
        showMessage('请先选择要处理的文本', 'error');
        return;
    }

    const toolbar = document.getElementById('textSelectionToolbar');
    const originalContent = toolbar.innerHTML;

    // 显示处理状态
    toolbar.innerHTML = `
        <div class="ai-processing">
            <div class="spinner"></div>
            <span>AI正在处理中...</span>
        </div>
    `;

    try {
        // 构建完整的提示
        const fullPrompt = `${prompt}\n\n"${selectedText}"\n\n请直接返回处理后的内容，不要包含任何解释或说明。`;

        // 调用AI API
        const response = await fetch('/api/ai_text_process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: fullPrompt,
                action: action,
                original_text: selectedText
            })
        });

        const result = await response.json();

        if (response.ok && result.success && result.processed_text) {
            // 替换选中的文本
            replaceSelectedText(result.processed_text);
            showMessage(`${getActionName(action)}完成`, 'success');
        } else {
            throw new Error(result.error || `HTTP ${response.status}: AI处理失败`);
        }

    } catch (error) {
        console.error('AI处理错误:', error);
        showMessage(`${getActionName(action)}失败: ${error.message}`, 'error');

        // 恢复工具栏内容，让用户可以重试
        setTimeout(() => {
            toolbar.innerHTML = originalContent;
            bindToolbarEvents();
        }, 2000);
        return;
    }

    // 成功时恢复工具栏内容并隐藏
    toolbar.innerHTML = originalContent;
    bindToolbarEvents();
    hideToolbar();
}

// 替换选中的文本
function replaceSelectedText(newText) {
    if (!selectedRange) return;

    // 删除选中的内容
    selectedRange.deleteContents();

    // 创建新的文本节点
    const textNode = document.createTextNode(newText);

    // 插入新内容
    selectedRange.insertNode(textNode);

    // 清除选择
    window.getSelection().removeAllRanges();

    // 高亮显示新插入的内容
    highlightNewText(textNode);
}

// 高亮显示新插入的文本
function highlightNewText(textNode) {
    const span = document.createElement('span');
    span.className = 'selected-text-highlight';
    span.textContent = textNode.textContent;

    textNode.parentNode.replaceChild(span, textNode);

    // 3秒后移除高亮
    setTimeout(() => {
        if (span.parentNode) {
            const newTextNode = document.createTextNode(span.textContent);
            span.parentNode.replaceChild(newTextNode, span);
        }
    }, 3000);
}

// 获取操作名称
function getActionName(action) {
    const actionNames = {
        'expand': 'AI扩写',
        'improve': '改进写作',
        'summarize': '总结',
        'grammar': '语法检查',
        'simplify': '简化内容',
        'formalize': '丰富内容',
        'translate': '翻译',
        'explain': '解释',
        'custom': '自定义处理'
    };
    return actionNames[action] || '处理';
}

// 处理自定义提示
function processCustomPrompt() {
    const input = document.getElementById('customPromptInput');
    if (!input) return;

    const customPrompt = input.value.trim();
    if (customPrompt) {
        processTextWithAI('custom', customPrompt + '：');
        input.value = '';
    }
}

// 阻止输入框事件冒泡
function setupInputEventHandlers() {
    const input = document.getElementById('customPromptInput');
    if (input) {
        // 阻止点击事件冒泡，防止工具栏消失
        input.addEventListener('click', function(e) {
            e.stopPropagation();
        });

        // 阻止焦点事件冒泡
        input.addEventListener('focus', function(e) {
            e.stopPropagation();
        });

        // 回车键处理
        input.addEventListener('keypress', function(e) {
            e.stopPropagation();
            if (e.key === 'Enter') {
                processCustomPrompt();
            }
        });

        // 阻止其他键盘事件冒泡
        input.addEventListener('keydown', function(e) {
            e.stopPropagation();
        });

        input.addEventListener('keyup', function(e) {
            e.stopPropagation();
        });
    }
}

// 编辑模式状态
let isEditMode = false;

// 切换编辑模式
function toggleEditMode() {
    isEditMode = !isEditMode;
    const minutesContent = document.getElementById('minutesContent');
    const editToggle = document.querySelector('.edit-toggle');

    if (isEditMode) {
        // 启用编辑模式
        minutesContent.contentEditable = true;
        minutesContent.classList.add('editable-content');
        editToggle.classList.add('active');
        editToggle.innerHTML = '<i class="fas fa-save"></i> 保存';

        // 显示编辑指示器
        showEditIndicator();

        // 隐藏工具栏
        hideToolbar();

        showMessage('编辑模式已启用，您可以直接编辑文本', 'success');
    } else {
        // 禁用编辑模式
        minutesContent.contentEditable = false;
        minutesContent.classList.remove('editable-content');
        editToggle.classList.remove('active');
        editToggle.innerHTML = '<i class="fas fa-edit"></i> 编辑模式';

        // 隐藏编辑指示器
        hideEditIndicator();

        showMessage('编辑模式已关闭，更改已保存', 'success');
    }
}

// 显示编辑指示器
function showEditIndicator() {
    let indicator = document.getElementById('editIndicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'editIndicator';
        indicator.className = 'edit-indicator';
        indicator.innerHTML = '<i class="fas fa-edit"></i> 编辑模式';
        document.body.appendChild(indicator);
    }
    indicator.style.display = 'flex';
}

// 隐藏编辑指示器
function hideEditIndicator() {
    const indicator = document.getElementById('editIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// 在页面加载时初始化文本选择工具栏
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保其他组件已加载
    setTimeout(() => {
        initializeTextSelectionToolbar();
    }, 1000);
});

// ==================== AI优化功能 ====================

// 显示AI优化对话框
function showAIOptimizeDialog() {
    const modal = document.getElementById('aiOptimizeModal');
    const input = document.getElementById('aiOptimizeInput');

    if (modal && input) {
        modal.style.display = 'flex';
        input.value = '';
        input.focus();
    }
}

// 关闭AI优化对话框
function closeAIOptimizeDialog() {
    const modal = document.getElementById('aiOptimizeModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 生成优化的提示词
async function generateOptimizedPrompt() {
    const input = document.getElementById('aiOptimizeInput');
    const generateBtn = document.getElementById('generateBtn');

    if (!input || !generateBtn) return;

    const userRequirement = input.value.trim();
    if (!userRequirement) {
        showMessage('请描述您的会议纪要需求', 'error');
        return;
    }

    // 设置加载状态
    generateBtn.disabled = true;
    generateBtn.classList.add('loading');
    generateBtn.innerHTML = '<i class="fas fa-spinner"></i> 生成中...';

    try {
        // 调用AI优化API
        const response = await fetch('/api/optimize_prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_requirement: userRequirement
            })
        });

        const data = await response.json();

        if (data.success) {
            // 更新提示词配置
            if (data.system_prompt) {
                document.getElementById('systemPrompt').value = data.system_prompt;
            }
            if (data.glossary) {
                document.getElementById('glossary').value = data.glossary;
            }

            // 关闭对话框
            closeAIOptimizeDialog();

            // 显示成功消息
            showMessage('AI优化配置生成成功！请检查并保存配置。', 'success');

            // 高亮显示更新的字段
            highlightUpdatedFields();

        } else {
            showMessage(data.error || 'AI优化失败，请重试', 'error');
        }

    } catch (error) {
        console.error('AI优化失败:', error);
        showMessage('AI优化失败，请检查网络连接', 'error');
    } finally {
        // 恢复按钮状态
        generateBtn.disabled = false;
        generateBtn.classList.remove('loading');
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> 生成配置';
    }
}

// 高亮显示更新的字段
function highlightUpdatedFields() {
    const systemPrompt = document.getElementById('systemPrompt');
    const glossary = document.getElementById('glossary');

    [systemPrompt, glossary].forEach(field => {
        if (field) {
            field.style.borderColor = '#667eea';
            field.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';

            // 3秒后恢复正常样式
            setTimeout(() => {
                field.style.borderColor = '';
                field.style.boxShadow = '';
            }, 3000);
        }
    });
}

// 点击模态框外部关闭
document.addEventListener('click', function(e) {
    const modal = document.getElementById('aiOptimizeModal');
    if (modal && e.target === modal) {
        closeAIOptimizeDialog();
    }
});

// ESC键关闭模态框
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeAIOptimizeDialog();
    }
});

// 检查配置状态
async function checkConfigurationStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.missing_configs && data.missing_configs.length > 0) {
            showConfigurationWarning(data.missing_configs);
        }

        // 更新UI状态
        updateConfigurationStatus(data.config_status);

    } catch (error) {
        console.error('检查配置状态失败:', error);
    }
}

// 显示配置警告
function showConfigurationWarning(missingConfigs) {
    const warningHtml = `
        <div class="config-warning">
            <div class="warning-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="warning-content">
                <h3>系统配置不完整</h3>
                <p>以下配置项需要设置才能正常使用系统功能：</p>
                <ul>
                    ${missingConfigs.map(config => `<li>${config}</li>`).join('')}
                </ul>
                <button class="config-btn" onclick="openSettings()">
                    <i class="fas fa-cog"></i>
                    立即配置
                </button>
            </div>
        </div>
    `;

    // 在欢迎界面显示警告
    const welcomeSection = document.getElementById('welcomeSection');
    if (welcomeSection) {
        const existingWarning = welcomeSection.querySelector('.config-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
        welcomeSection.insertAdjacentHTML('afterbegin', warningHtml);
    }
}

// 更新配置状态
function updateConfigurationStatus(configStatus) {
    // 更新系统设置按钮的状态
    const settingsBtn = document.querySelector('.settings-btn');
    if (settingsBtn) {
        const hasIncompleteConfig = Object.values(configStatus).some(status => !status);
        if (hasIncompleteConfig) {
            settingsBtn.classList.add('has-warning');
            settingsBtn.title = '系统配置不完整，点击配置';
        } else {
            settingsBtn.classList.remove('has-warning');
            settingsBtn.title = '系统设置';
        }
    }
}


