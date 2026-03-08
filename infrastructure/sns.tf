# SNS Topics for Notifications

# Topic for pending approvals
resource "aws_sns_topic" "pending_approvals" {
  name              = "${var.project_name}-pending-approvals"
  display_name      = "Accounting Copilot - Pending Approvals"
  kms_master_key_id = "alias/aws/sns"

  tags = local.common_tags
}

# Topic for OCR failures
resource "aws_sns_topic" "ocr_failures" {
  name              = "${var.project_name}-ocr-failures"
  display_name      = "Accounting Copilot - OCR Failures"
  kms_master_key_id = "alias/aws/sns"

  tags = local.common_tags
}

# Topic for unmatched transactions
resource "aws_sns_topic" "unmatched_transactions" {
  name              = "${var.project_name}-unmatched-transactions"
  display_name      = "Accounting Copilot - Unmatched Transactions"
  kms_master_key_id = "alias/aws/sns"

  tags = local.common_tags
}

# Topic for approval reminders
resource "aws_sns_topic" "approval_reminders" {
  name              = "${var.project_name}-approval-reminders"
  display_name      = "Accounting Copilot - Approval Reminders"
  kms_master_key_id = "alias/aws/sns"

  tags = local.common_tags
}

# Email subscription for admin (optional - can be added manually)
# Uncomment and set email to enable
# resource "aws_sns_topic_subscription" "admin_email" {
#   topic_arn = aws_sns_topic.pending_approvals.arn
#   protocol  = "email"
#   endpoint  = "admin@example.com"
# }
