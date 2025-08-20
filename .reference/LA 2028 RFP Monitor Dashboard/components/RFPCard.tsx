import { RFP } from '../types/rfp';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/card';
import { ExternalLink, Calendar, Building, DollarSign, Eye, EyeOff, Star } from 'lucide-react';
import { format } from '../utils/dateUtils';

interface RFPCardProps {
  rfp: RFP;
  onViewDetails: (rfp: RFP) => void;
  onIgnore: (id: string) => void;
  onToggleStar?: (id: string) => void;
  isIgnored?: boolean;
  isStarred?: boolean;
}

export function RFPCard({ 
  rfp, 
  onViewDetails, 
  onIgnore, 
  onToggleStar,
  isIgnored = false,
  isStarred = false 
}: RFPCardProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'closing_soon':
        return 'destructive';
      case 'active':
        return 'default';
      case 'closed':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getEventAssociationColor = (association: string) => {
    switch (association) {
      case 'Olympics 2028':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-200';
      case 'World Cup 2026':
        return 'bg-green-100 text-green-800 hover:bg-green-200';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
    }
  };

  const getProcurementTypeColor = (type: string) => {
    switch (type) {
      case 'Technology':
        return 'bg-purple-100 text-purple-800 hover:bg-purple-200';
      case 'Construction':
        return 'bg-orange-100 text-orange-800 hover:bg-orange-200';
      case 'Services':
        return 'bg-cyan-100 text-cyan-800 hover:bg-cyan-200';
      case 'Equipment':
        return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
    }
  };

  return (
    <Card className={`group hover:shadow-lg transition-all duration-200 ${isIgnored ? 'opacity-60 grayscale' : ''} relative`}>
      {/* Star button in top right corner */}
      {onToggleStar && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onToggleStar(rfp.id)}
          className={`absolute top-2 right-2 z-10 p-1 h-auto w-auto ${
            isStarred 
              ? 'text-yellow-500 hover:text-yellow-600' 
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Star className={`h-4 w-4 ${isStarred ? 'fill-current' : ''}`} />
        </Button>
      )}

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2 pr-8">
          <CardTitle 
            className="cursor-pointer hover:text-primary transition-colors line-clamp-2"
            onClick={() => onViewDetails(rfp)}
          >
            {rfp.title}
          </CardTitle>
          <Badge variant={getStatusBadgeVariant(rfp.status)}>
            {rfp.status.replace('_', ' ')}
          </Badge>
        </div>
        
        <div className="flex flex-wrap gap-2 mt-2">
          {rfp.event_association && (
            <Badge 
              variant="outline" 
              className={getEventAssociationColor(rfp.event_association)}
            >
              {rfp.event_association}
            </Badge>
          )}
          {rfp.procurement_type && (
            <Badge 
              variant="outline" 
              className={getProcurementTypeColor(rfp.procurement_type)}
            >
              {rfp.procurement_type}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <p className="text-muted-foreground line-clamp-3 mb-3">
          {rfp.description}
        </p>
        
        <div className="space-y-2">
          {rfp.issuer && (
            <div className="flex items-center gap-2 text-sm">
              <Building className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{rfp.issuer}</span>
            </div>
          )}
          
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">
              Posted: {format(new Date(rfp.posted_date), 'MMM dd, yyyy')}
            </span>
          </div>
          
          {rfp.closing_date && (
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-destructive" />
              <span className="text-destructive">
                Closes: {format(new Date(rfp.closing_date), 'MMM dd, yyyy')}
              </span>
            </div>
          )}
          
          {rfp.contract_value && (
            <div className="flex items-center gap-2 text-sm">
              <DollarSign className="h-4 w-4 text-green-600" />
              <span className="font-medium text-green-600">
                {formatCurrency(rfp.contract_value)}
              </span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="pt-0 flex flex-col gap-2">
        {/* Main action buttons */}
        <div className="flex w-full gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => onViewDetails(rfp)}
            className="flex-1"
          >
            View Details
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            asChild
            className="flex-1"
          >
            <a 
              href={rfp.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-1"
            >
              <ExternalLink className="h-3 w-3" />
              Source
            </a>
          </Button>
        </div>

        {/* Secondary action button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onIgnore(rfp.id)}
          className="w-full text-muted-foreground hover:text-foreground"
        >
          {isIgnored ? (
            <>
              <Eye className="h-4 w-4 mr-1" />
              Restore
            </>
          ) : (
            <>
              <EyeOff className="h-4 w-4 mr-1" />
              Ignore
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}