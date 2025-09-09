$(document).ready(function() {
    // التحقق من وجود العناصر قبل استخدامها
    let currentIndexElement = $('#current_index');
    let currentQuestionIndex = currentIndexElement.length > 0 ? parseInt(currentIndexElement.val() || 0) : 0;
    let totalQuestions = $('.question-section').length;

    // إخفاء جميع الأسئلة عدا السؤال الحالي عند التحميل
    $('.question-section').hide();
    let currentQuestion = $('.question-section').eq(currentQuestionIndex);
    if (currentQuestion.length > 0) {
        currentQuestion.show();
    }

    // تحديث نص التقدم
    updateProgressText(currentQuestionIndex);

    // إظهار/إخفاء أزرار التنقل حسب الموقع
    updateNavigationButtons();

    // مراقبة تغييرات الإدخال للأسئلة
    setupInputChangeListeners();

    // معالجة النقر على زر التالي
    $('#next_button').on('click', function() {
        if (currentQuestionIndex < totalQuestions - 1) {
            // إخفاء السؤال الحالي
            $('.question-section').hide();

            // زيادة المؤشر للانتقال للسؤال التالي
            currentQuestionIndex++;

            // عرض السؤال التالي
            $('.question-section').eq(currentQuestionIndex).show();

            // تحديث نص التقدم
            updateProgressText(currentQuestionIndex);

            // تحديث حالة الأزرار
            updateNavigationButtons();

            // إعادة إعداد مراقبة التغييرات
            setupInputChangeListeners();

            // إضافة تفعيل النقر على كامل مساحة الخيار عند التنقل
            setupClickableOptions();
        }
    });

    // معالجة النقر على زر السابق
    $('#prev_button').on('click', function() {
        if (currentQuestionIndex > 0) {
            // إخفاء السؤال الحالي
            $('.question-section').hide();

            // تقليل المؤشر للعودة للسؤال السابق
            currentQuestionIndex--;

            // عرض السؤال السابق
            $('.question-section').eq(currentQuestionIndex).show();

            // تحديث نص التقدم
            updateProgressText(currentQuestionIndex);

            // تحديث حالة الأزرار
            updateNavigationButtons();

            // تمكين زر التالي دائمًا عند العودة لسؤال سابق (لأنه تمت الإجابة عليه سابقًا)
            $('#next_button').prop('disabled', false);

            // إضافة تفعيل النقر على كامل مساحة الخيار عند التنقل
            setupClickableOptions();
        }
    });

    // وظيفة لتحديث نص التقدم
    function updateProgressText(index) {
        $('.progress-text').text((index + 1) + ' من ' + totalQuestions + ' أسئلة');
    }

    // وظيفة لإعداد مراقبة تغييرات الإدخال
    function setupInputChangeListeners() {
        // إلغاء المراقبات السابقة أولاً
        $('.answer-input').off('change input');

        // إعادة إعداد المراقبات للسؤال الحالي
        let currentAnswerInputs = $('.question-section').eq(currentQuestionIndex).find('.answer-input');
        let currentSection = $('.question-section').eq(currentQuestionIndex);

        // للأزرار الراديو
        currentAnswerInputs.filter('input[type="radio"]').on('change', function() {
            if (currentQuestionIndex === totalQuestions - 1) {
                $('#submit_button').prop('disabled', false);
            } else {
                $('#next_button').prop('disabled', false);
            }
        });

        // للمربعات - تحقق من وجود مربع واحد على الأقل محدد
        currentAnswerInputs.filter('input[type="checkbox"]').on('change', function() {
            // التحقق من وجود مربع واحد محدد على الأقل
            let hasCheckedBox = currentSection.find('input[type="checkbox"]:checked').length > 0;

            if (currentQuestionIndex === totalQuestions - 1) {
                $('#submit_button').prop('disabled', !hasCheckedBox);
            } else {
                $('#next_button').prop('disabled', !hasCheckedBox);
            }
        });

        // للنصوص
        currentAnswerInputs.filter('textarea').on('input', function() {
            let hasText = $(this).val() && $(this).val().trim() !== '';
            if (currentQuestionIndex === totalQuestions - 1) {
                $('#submit_button').prop('disabled', !hasText);
            } else {
                $('#next_button').prop('disabled', !hasText);
            }
        });

        // التحقق من وجود إجابات مسبقة وتحديث حالة الأزرار
        checkForExistingAnswers();
    }

    // وظيفة للتحقق من وجود إجابات مسبقة
    function checkForExistingAnswers() {
        let currentSection = $('.question-section').eq(currentQuestionIndex);

        // التحقق من نوع السؤال وحالة الإجابات
        let hasRadioAnswer = currentSection.find('input[type="radio"]:checked').length > 0;
        let hasCheckedBox = currentSection.find('input[type="checkbox"]:checked').length > 0;

        // التعامل مع النصوص
        let textareaValue = currentSection.find('textarea.answer-input').val();
        let hasTextAnswer = textareaValue && textareaValue.trim() !== '';

        // تحديث حالة الأزرار حسب نوع السؤال
        let hasValidAnswer = false;

        if (currentSection.find('input[type="radio"]').length > 0) {
            hasValidAnswer = hasRadioAnswer;
        } else if (currentSection.find('input[type="checkbox"]').length > 0) {
            hasValidAnswer = hasCheckedBox;
        } else if (currentSection.find('textarea').length > 0) {
            hasValidAnswer = hasTextAnswer;
        }

        // تحديث حالة الأزرار
        if (currentQuestionIndex === totalQuestions - 1) {
            $('#submit_button').prop('disabled', !hasValidAnswer);
        } else {
            $('#next_button').prop('disabled', !hasValidAnswer);
        }
    }

    // وظيفة لتحديث حالة أزرار التنقل
    function updateNavigationButtons() {
        // تعطيل/تمكين زر السابق
        $('#prev_button').prop('disabled', currentQuestionIndex === 0);

        // إظهار/إخفاء زر التسليم
        if (currentQuestionIndex === totalQuestions - 1) {
            // في السؤال الأخير، يتم تغيير زر التالي إلى زر التسليم
            $('#next_button').hide();
            $('#submit_button').show();

            // افتراضيًا، زر التسليم معطل حتى يتم اختيار إجابة
            $('#submit_button').prop('disabled', true);

            // تحقق من وجود إجابة مسبقة
            checkForExistingAnswers();
        } else {
            // في الأسئلة الأخرى، يظهر زر التالي ويختفي زر التسليم
            $('#next_button').show();
            $('#submit_button').hide();

            // افتراضيًا، زر التالي معطل حتى يتم اختيار إجابة
            $('#next_button').prop('disabled', true);

            // تحقق من وجود إجابة مسبقة
            checkForExistingAnswers();
        }
    }


    // وظيفة جديدة لجعل كامل مساحة الخيار قابلة للنقر
    function setupClickableOptions() {
        // إضافة نمط المؤشر للخيارات لتبدو قابلة للنقر
        $('.option-item').css('cursor', 'pointer');

        // إلغاء التسجيل السابق لتجنب تعدد التسجيل
        $('.option-item').off('click');

        // تسجيل حدث النقر على كامل مساحة الخيار
        $('.option-item').on('click', function(e) {
            // تجاهل النقر على عنصر الإدخال نفسه لتجنب الازدواجية
            if (e.target.tagName !== 'INPUT') {
                // البحث عن عنصر الإدخال داخل الخيار
                const inputElement = $(this).find('input.answer-input');

                // تحديد نوع الإدخال والتعامل معه
                if (inputElement.attr('type') === 'radio') {
                    // تحديد الراديو بتون
                    inputElement.prop('checked', true);
                } else if (inputElement.attr('type') === 'checkbox') {
                    // تبديل حالة الشيك بوكس
                    inputElement.prop('checked', !inputElement.prop('checked'));
                }

                // إطلاق حدث التغيير لتفعيل الكود الأصلي
                inputElement.trigger('change');
            }
        });
    }

    // تفعيل النقر على كامل مساحة الخيار عند بدء التحميل
    setupClickableOptions();
});