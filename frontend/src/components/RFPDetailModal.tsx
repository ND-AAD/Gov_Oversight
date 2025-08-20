import type { RFP } from '../types/rfp';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Separator } from './ui/separator';
import { 
  ExternalLink, 
  Calendar, 
  Building, 
  DollarSign, 
  EyeOff, 
  Star,
  Globe,
  Clock,
  Tag,
  FileText
} from 'lucide-react';

interface RFPDetailModalProps {
  rfp: RFP;
  isOpen: boolean;
  onClose: () => void;
  onIgnore: (id: string) => void;
  onToggleStar?: (id: string) => void;
  isIgnored?: boolean;
  isStarred?: boolean;
}

export function RFPDetailModal({
  rfp,
  isOpen,
  onClose,
  onIgnore,
  onToggleStar,
  isIgnored = false,
  isStarred = false
}: RFPDetailModalProps) {
  const formatCurrency = (amount: number) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const formatDateTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getExtractedValue = (field: string) => {
    return rfp.extracted_fields?.[field] || '';
  };

  const isPriority = rfp.categories.some(cat => 
    cat.toLowerCase().includes('surveillance') || 
    cat.toLowerCase().includes('security') ||
    cat.toLowerCase().includes('technology')
  );

  const isClosingSoon = rfp.closing_date ? (() => {
    const closingDate = new Date(rfp.closing_date);
    const threeDaysFromNow = new Date();
    threeDaysFromNow.setDate(threeDaysFromNow.getDate() + 3);
    return closingDate <= threeDaysFromNow;
  })() : false;

  const contractValue = getExtractedValue('contract_value');
  const issuer = getExtractedValue('issuer');
  const eventAssociation = getExtractedValue('event_association');
  const procurementType = getExtractedValue('procurement_type');
  const status = getExtractedValue('status');

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-xl leading-7 mb-2">
                {rfp.title}
              </DialogTitle>
              <div className="flex flex-wrap gap-2 mb-4">
                {isPriority && (
                  <Badge variant="destructive">
                    High Priority Surveillance
                  </Badge>
                )}
                {isClosingSoon && (
                  <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                    Closing Soon
                  </Badge>
                )}
                {status && (
                  <Badge 
                    variant={status === 'active' ? 'default' : 
                            status === 'closing_soon' ? 'secondary' : 'outline'}
                  >
                    {status.replace('_', ' ').toUpperCase()}
                  </Badge>
                )}
                {eventAssociation && (
                  <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                    {eventAssociation}
                  </Badge>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-2 ml-4">
              {onToggleStar && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onToggleStar(rfp.id)}
                >
                  <Star className={`w-5 h-5 ${
                    isStarred ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'
                  }`} />
                </Button>
              )}
              {!isIgnored && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    onIgnore(rfp.id);
                    onClose();
                  }}
                  className="text-gray-500 hover:text-red-600"
                >
                  <EyeOff className="w-5 h-5" />
                </Button>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Key Information Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                  <Building className="w-4 h-4" />
                  <span>Source Site</span>
                </label>
                <p className="text-base font-medium">{rfp.source_site}</p>
              </div>

              {issuer && (
                <div>
                  <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                    <Building className="w-4 h-4" />
                    <span>Issuing Organization</span>
                  </label>
                  <p className="text-base font-medium">{issuer}</p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                  <Calendar className="w-4 h-4" />
                  <span>Posted Date</span>
                </label>
                <p className="text-base">{formatDate(rfp.posted_date)}</p>
              </div>

              {rfp.closing_date && (
                <div>
                  <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                    <Clock className="w-4 h-4" />
                    <span>Closing Date</span>
                  </label>
                  <p className={`text-base font-medium ${
                    isClosingSoon ? 'text-red-600' : 'text-gray-900'
                  }`}>
                    {formatDate(rfp.closing_date)}
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-4">
              {contractValue && (
                <div>
                  <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                    <DollarSign className="w-4 h-4" />
                    <span>Contract Value</span>
                  </label>
                  <p className="text-base font-semibold text-green-600">
                    {formatCurrency(Number(contractValue))}
                  </p>
                </div>
              )}

              {procurementType && (
                <div>
                  <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                    <Tag className="w-4 h-4" />
                    <span>Procurement Type</span>
                  </label>
                  <p className="text-base">{procurementType}</p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                  <Globe className="w-4 h-4" />
                  <span>Content Hash</span>
                </label>
                <p className="text-sm font-mono text-gray-600">{rfp.content_hash}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-1">
                  <Clock className="w-4 h-4" />
                  <span>Detected At</span>
                </label>
                <p className="text-sm text-gray-600">{formatDateTime(rfp.detected_at)}</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Description */}
          <div>
            <label className="text-sm font-medium text-gray-500 flex items-center space-x-1 mb-3">
              <FileText className="w-4 h-4" />
              <span>Description</span>
            </label>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {rfp.description}
              </p>
            </div>
          </div>

          {/* Categories */}
          {rfp.categories.length > 0 && (
            <div>
              <label className="text-sm font-medium text-gray-500 mb-3 block">Categories</label>
              <div className="flex flex-wrap gap-2">
                {rfp.categories.map((category) => (
                  <Badge 
                    key={category} 
                    variant="outline"
                    className={`${
                      category.toLowerCase().includes('surveillance') || 
                      category.toLowerCase().includes('security') 
                        ? 'border-red-200 text-red-700 bg-red-50' 
                        : ''
                    }`}
                  >
                    {category}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Additional Extracted Fields */}
          {Object.keys(rfp.extracted_fields || {}).length > 0 && (
            <div>
              <label className="text-sm font-medium text-gray-500 mb-3 block">Additional Information</label>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(rfp.extracted_fields || {}).map(([key, value]) => (
                    <div key={key} className="space-y-1">
                      <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        {key.replace(/_/g, ' ')}
                      </label>
                      <p className="text-sm text-gray-800">
                        {typeof value === 'number' && key.toLowerCase().includes('value') 
                          ? formatCurrency(value)
                          : String(value)
                        }
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Change History */}
          {rfp.change_history && rfp.change_history.length > 0 && (
            <div>
              <label className="text-sm font-medium text-gray-500 mb-3 block">Change History</label>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                {rfp.change_history.map((change, index) => (
                  <div key={index} className="border-l-2 border-blue-200 pl-3">
                    <p className="text-sm font-medium text-gray-800">
                      {change.field}: {change.oldValue} → {change.newValue}
                    </p>
                    <p className="text-xs text-gray-500">{formatDateTime(change.timestamp)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Separator />

          {/* Actions */}
          <div className="flex items-center justify-between">
            <Button
              onClick={() => window.open(rfp.url, '_blank')}
              className="flex items-center space-x-2"
            >
              <ExternalLink className="w-4 h-4" />
              <span>View Original RFP</span>
            </Button>

            <div className="flex items-center space-x-2">
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
